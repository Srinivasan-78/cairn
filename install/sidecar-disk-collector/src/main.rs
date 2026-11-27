use serde::Serialize;
use std::env;
use std::fs;
use std::path::Path;
use std::process::Command;
use std::thread;
use std::time::Duration;

const PSEUDO_FS: &[&str] = &[
    "tmpfs",
    "devtmpfs",
    "squashfs",
    "sysfs",
    "proc",
    "devpts",
    "cgroup",
    "cgroup2",
    "overlay",
    "nsfs",
    "autofs",
    "hugetlbfs",
    "mqueue",
    "pstore",
    "fusectl",
    "binfmt_misc",
];

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct FsEntry {
    pub fs: String,
    pub size: u64,
    pub used: u64,
    pub available: u64,
    #[serde(rename = "use")]
    pub use_pct: u64,
    pub mount: String,
}

#[derive(Debug, Clone)]
pub struct MountRecord {
    pub dev: String,
    pub mountpoint: String,
    pub fstype: String,
}

pub fn parse_mounts(content: &str) -> Vec<MountRecord> {
    content
        .lines()
        .filter_map(|line| {
            let mut parts = line.split_whitespace();
            let dev = parts.next()?;
            let mountpoint = parts.next()?;
            let fstype = parts.next()?;
            if PSEUDO_FS.contains(&fstype) || mountpoint == "none" {
                return None;
            }
            Some(MountRecord {
                dev: dev.to_string(),
                mountpoint: mountpoint.to_string(),
                fstype: fstype.to_string(),
            })
        })
        .collect()
}

pub fn parse_df_line(line: &str) -> Option<(String, u64, u64, u64, u64)> {
    let parts: Vec<&str> = line.split_whitespace().collect();
    if parts.len() < 5 {
        return None;
    }
    let fs = parts[0].to_string();
    let size = parts[1].parse::<u64>().ok()?;
    let used = parts[2].parse::<u64>().ok()?;
    let avail = parts[3].parse::<u64>().ok()?;
    let pct = parts[4].trim_end_matches('%').parse::<u64>().ok()?;
    Some((fs, size, used, avail, pct))
}

fn df_stats(target: &str) -> Option<(String, u64, u64, u64, u64)> {
    let out = Command::new("df")
        .args(["-P", "-B1", target])
        .output()
        .ok()?;
    if !out.status.success() {
        return None;
    }
    let txt = String::from_utf8_lossy(&out.stdout);
    let line = txt.lines().nth(1)?;
    parse_df_line(line)
}

fn collect_once(storage_dir: &Path) {
    let disk_layout: serde_json::Value = Command::new("lsblk")
        .args([
            "--sysroot",
            "/host",
            "--json",
            "-b",
            "-o",
            "NAME,SIZE,TYPE,MODEL,SERIAL,VENDOR,ROTA,TRAN",
        ])
        .output()
        .ok()
        .filter(|o| o.status.success())
        .and_then(|o| serde_json::from_slice(&o.stdout).ok())
        .unwrap_or_else(|| serde_json::json!({ "blockdevices": [] }));

    let mut fs_entries = Vec::new();
    if let Ok(mounts_txt) = fs::read_to_string("/host/proc/1/mounts") {
        for m in parse_mounts(&mounts_txt) {
            let host_mount = format!("/host{}", m.mountpoint);
            if Path::new(&host_mount).is_file() {
                continue;
            }
            if let Some((_, size, used, available, use_pct)) = df_stats(&host_mount) {
                fs_entries.push(FsEntry {
                    fs: m.dev,
                    size,
                    used,
                    available,
                    use_pct,
                    mount: m.mountpoint,
                });
            }
        }
    }

    if fs_entries.is_empty() {
        let storage_str = storage_dir.to_string_lossy();
        if let Some((dev, size, used, available, use_pct)) = df_stats(&storage_str) {
            fs_entries.push(FsEntry {
                fs: dev,
                size,
                used,
                available,
                use_pct,
                mount: storage_str.into_owned(),
            });
        }
    }

    let payload = serde_json::json!({
        "diskLayout": disk_layout,
        "fsSize": fs_entries,
    });
    let tmp_path = storage_dir.join("cairn-disk-info.json.tmp");
    let final_path = storage_dir.join("cairn-disk-info.json");
    if let Ok(json) = serde_json::to_string_pretty(&payload) {
        if fs::write(&tmp_path, format!("{json}\n")).is_ok() {
            let _ = fs::rename(&tmp_path, &final_path);
        }
    }
}

fn main() {
    let storage_dir = env::var("CAIRN_STORAGE_DIR").unwrap_or_else(|_| "/storage".to_string());
    let storage_path = Path::new(&storage_dir);
    let _ = fs::create_dir_all(storage_path);
    let final_path = storage_path.join("cairn-disk-info.json");
    if !final_path.exists() {
        let _ = fs::write(
            &final_path,
            "{\"diskLayout\":{\"blockdevices\":[]},\"fsSize\":[]}\n",
        );
    }

    let once = env::args().any(|a| a == "--once");
    loop {
        collect_once(storage_path);
        if once {
            break;
        }
        thread::sleep(Duration::from_secs(120));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn filters_pseudo_filesystems_and_parses_df() {
        let mounts = "proc /proc proc rw 0 0\ntmpfs /run tmpfs rw 0 0\n/dev/sda1 / ext4 rw 0 0\n";
        let parsed = parse_mounts(mounts);
        assert_eq!(parsed.len(), 1);
        assert_eq!(parsed[0].dev, "/dev/sda1");
        assert_eq!(parsed[0].mountpoint, "/");

        let df = parse_df_line("/dev/sda1 1000000 400000 600000 40% /").unwrap();
        assert_eq!(df.0, "/dev/sda1");
        assert_eq!(df.1, 1_000_000);
        assert_eq!(df.4, 40);
    }
}
