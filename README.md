<div align="center">

# Cairn
### Knowledge That Never Goes Offline

</div>

---

> **Origin & credits.** Cairn is a derivative work built on **[Project NOMAD](https://github.com/Crosstalk-Solutions/project-nomad)**
> by **Crosstalk Solutions, LLC** (started in 2025 by Chris Sherwood), used under the Apache License 2.0.
> The full inspiration and the overwhelming majority of this codebase are theirs — all credit for the
> original design and implementation goes to the Project NOMAD team and its contributors.
>
> Cairn is an independent fork and is **not affiliated with, endorsed by, or sponsored by Crosstalk
> Solutions**. Per Apache-2.0 §6, the upstream project's marks are not used as Cairn's branding: the
> "Project NOMAD" / "NOMAD" name, its logo, `projectnomad.us`, the Discord server, and the hosted
> benchmark leaderboard have been removed or replaced with placeholders. Some hosted-service URLs point
> at the reserved `cairn.example` domain and are non-functional until Cairn stands up its own backends.
> See [`NOTICE`](NOTICE) for the full attribution and list of modifications, and [`LICENSE`](LICENSE) for terms.

Cairn is a self-contained, offline-first knowledge and education server packed with critical tools, knowledge, and AI to keep you informed and empowered — anytime, anywhere.

## Installation & Quickstart
Cairn can be installed on any Debian-based operating system (we recommend Ubuntu 26.04 LTS; 24.04 LTS and Debian 12 are also supported). Installation is completely terminal-based, and all tools and resources are designed to be accessed through the browser, so there's no need for a desktop environment if you'd rather setup Cairn as a "server" and access it through other clients.

*Note: sudo/root privileges are required to run the install script*

### Quick Install (Debian-based OS Only)
```bash
sudo apt-get update && \
sudo apt-get install -y curl && \
curl -fsSL https://raw.githubusercontent.com/Srinivasan-78/cairn/refs/heads/main/install/install_cairn.sh \
  -o install_cairn.sh && \
sudo bash install_cairn.sh
```

Cairn is now installed on your device! Open a browser and navigate to `http://localhost:8080` (or `http://DEVICE_IP:8080`) to start exploring!

For a complete step-by-step walkthrough (including Ubuntu installation), see the [Installation Guide](https://cairn.example/install). For Windows users, see the [WSL2 install guide](https://cairn.example/install/wsl2) — community-supported path covering native Docker and Docker Desktop install routes.

### Advanced Installation
For more control over the installation process, copy and paste the [Docker Compose template](https://raw.githubusercontent.com/Srinivasan-78/cairn/refs/heads/main/install/management_compose.yaml) into a `docker-compose.yml` file and customize it to your liking (be sure to replace any placeholders with your actual values). Then, run `docker compose up -d` to start the Command Center and its dependencies. Note: this method is recommended for advanced users only, as it requires familiarity with Docker and manual configuration before starting.

## How It Works
Cairn is a management UI ("Command Center") and API that orchestrates a collection of containerized tools and resources via [Docker](https://www.docker.com/). It handles installation, configuration, and updates for everything — so you don't have to.

**Built-in capabilities include:**
- **AI Chat with Knowledge Base** — local AI chat powered by [Ollama](https://ollama.com/) or you can use OpenAI API compatible software such as LM Studio or llama.cpp, with document upload and semantic search (RAG via [Qdrant](https://qdrant.tech/))
- **Information Library** — offline Wikipedia, medical references, ebooks, and more via [Kiwix](https://kiwix.org/)
- **Education Platform** — Khan Academy courses with progress tracking via [Kolibri](https://learningequality.org/kolibri/)
- **Offline Maps** — downloadable regional maps via [ProtoMaps](https://protomaps.com)
- **Data Tools** — encryption, encoding, and analysis via [CyberChef](https://gchq.github.io/CyberChef/)
- **Notes** — local note-taking via [FlatNotes](https://github.com/dullage/flatnotes)
- **System Benchmark** — hardware scoring with a [community leaderboard](https://benchmark.cairn.example)
- **Supply Depot** — a one-click app catalog (PDF tools, file browser, e-book library, password manager, and more) plus the ability to run your own custom Docker containers
- **Automatic Updates** — opt-in, hands-off updates for the core software, installed apps, and offline content, on a schedule you control
- **Easy Setup Wizard** — guided first-time configuration with curated content collections

Cairn also includes built-in tools like a Wikipedia content selector, ZIM library manager, and content explorer.

## What's Included

| Capability | Powered By | What You Get |
|-----------|-----------|-------------|
| Information Library | Kiwix | Offline Wikipedia, medical references, survival guides, ebooks |
| AI Assistant | Ollama + Qdrant | Built-in chat with document upload and semantic search |
| Education Platform | Kolibri | Khan Academy courses, progress tracking, multi-user support |
| Offline Maps | ProtoMaps | Downloadable regional maps for offline viewing and search |
| Data Tools | CyberChef | Encryption, encoding, hashing, and data analysis |
| Notes | FlatNotes | Local note-taking with markdown support |
| System Benchmark | Built-in | Hardware scoring, Builder Tags, and community leaderboard |
| Supply Depot | Built-in | One-click app catalog + bring-your-own custom Docker containers |

## Device Requirements
While many similar offline survival computers are designed to be run on bare-minimum, lightweight hardware, Cairn is quite the opposite. To install and run the
available AI tools, we highly encourage the use of a beefy, GPU-backed device to make the most of your install.

At its core, however, Cairn is still very lightweight. For a barebones installation of the management application itself, the following minimal specs are required:

*Note: Cairn is not sponsored by any hardware manufacturer and is designed to be as hardware-agnostic as possible. The hardware listed below is for example/comparison use only*

#### Minimum Specs
- Processor: 2 GHz dual-core processor or better
- RAM: 4GB system memory
- Storage: At least 5 GB free disk space
- OS: Debian-based (Ubuntu 26.04 LTS recommended)
- Stable internet connection (required during install only)

To run LLMs and other included AI tools:

#### Optimal Specs
- Processor: AMD Ryzen 7 or Intel Core i7 or better
- RAM: 32 GB system memory
- Graphics: NVIDIA RTX 3060 or AMD equivalent or better (more VRAM = run larger models)
- Storage: At least 250 GB free disk space (preferably on SSD)
- OS: Debian-based (Ubuntu 26.04 LTS recommended)
- Stable internet connection (required during install only)

**For detailed build recommendations at three price points ($150–$1,000+), see the [Hardware Guide](https://cairn.example/hardware).**

Again, Cairn itself is quite lightweight — it's the tools and resources you choose to install with Cairn that will determine the specs required for your unique deployment

#### Running AI models on a different host
By default, Cairn's installer will attempt to setup Ollama on the host when the AI Assistant is installed. However, if you would like to run the AI model on a different host, you can go to the settings of the AI assistant and input a URL for either an ollama or OpenAI-compatible API server (such as LM Studio).  
Note that if you use Ollama on a different host, you must start the server with this option: `OLLAMA_HOST=0.0.0.0`.  
Ollama is the preferred way to use the AI assistant, as it has features such as model download that OpenAI API does not support. So when using LM Studio, for example, you will have to use LM Studio to download models.
You are responsible for the setup of Ollama/OpenAI server on the other host.

## Frequently Asked Questions (FAQ)
For answers to common questions about Cairn, please see our [FAQ](FAQ.md) page.

## About Internet Usage & Privacy
Cairn is designed for offline usage. An internet connection is only required during the initial installation (to download dependencies) and if you (the user) decide to download additional tools and resources at a later time. Otherwise, Cairn does not require an internet connection and has ZERO built-in telemetry.

To test internet connectivity, Cairn first attempts to make a request to Cloudflare's utility endpoint, `https://1.1.1.1/cdn-cgi/trace`. If that endpoint is unreachable (for example, because your network blocks `1.1.1.1`), it falls back to other endpoints the application already contacts (the GitHub API and the Cairn API) and considers the connection online if any of them respond.

You can override the endpoint used for this check in two ways. The connectivity test URL can be configured from the UI under **Settings → Advanced** (stored locally on your instance), or you can set the `INTERNET_STATUS_TEST_URL` environment variable. When set, the environment variable always takes precedence over the UI-configured value. If neither is set, the built-in defaults above are used.

## About Security
By design, Cairn is intended to be open and available without hurdles — it includes no authentication. If you decide to connect your device to a local network after install (e.g. for allowing other devices to access its resources), you can block/open ports to control which services are exposed.

**Will authentication be added in the future?** Maybe. It's not currently a priority, but if there's enough demand for it, we may consider building in an optional authentication layer in a future release to support use cases where multiple users need access to the same instance but with different permission levels (e.g. family use with parental controls, classroom use with teacher/admin accounts, etc.). We have a suggestion for this on our public roadmap, so if this is something you'd like to see, please upvote it here: https://roadmap.cairn.example/posts/1/user-authentication-please-build-in-user-auth-with-admin-user-roles

For now, we recommend using network-level controls to manage access if you're planning to expose your Cairn instance to other devices on a local network. Cairn is not designed to be exposed directly to the internet, and we strongly advise against doing so unless you really know what you're doing, have taken appropriate security measures, and understand the risks involved.

## Contributing
Contributions are welcome and appreciated! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to the project.

### Testing Auto-Updates (Dry Run)

The Command Center can automatically install **minor/patch** updates of itself during a configurable window, after a cool-off period, and only when pre-flight checks pass (sufficient disk for the new image, no downloads or app installs in progress). Major versions always require a manual update.

Because exercising this logic with real version bumps is impractical, an Ace command runs the **entire decision pipeline without ever triggering an update**. Run it from the `admin/` directory:

```bash
# 1) Deterministic scenario suite — no network, DB, or Docker required.
#    Proves every branch (major-only, cool-off, prerelease/draft, window wrap, …)
#    and exits non-zero on failure, so it's safe to wire into CI.
node ace auto-update:dry-run --scenarios

# 2) Simulate "what would happen if I were running 1.32.0 right now?"
#    against the LIVE GitHub releases feed and real pre-flight checks:
node ace auto-update:dry-run --current=1.32.0 --force-enabled

# 3) Fully offline simulation with a canned release list and a fixed clock:
node ace auto-update:dry-run --current=1.32.0 --force-enabled \
  --releases-file=./fixtures/releases.json --now=2026-06-04T21:00:00Z \
  --window-start=20:00 --window-end=23:00 --cooloff=72 --skip-preflight
```

It prints the resolved decision — current version, whether the clock is inside the window, the eligible target (if any), and pre-flight blockers — ending in a clear verdict such as `WOULD UPDATE → v1.33.2` or `WOULD NOT UPDATE (outside-window): …`. **No real update is ever requested.**

| Flag | Description |
|------|-------------|
| `--scenarios` | Run the built-in deterministic scenario suite and exit |
| `--current=<version>` | Simulate this currently-running version (e.g. `1.32.0`) |
| `--force-enabled` | Treat auto-update as enabled, ignoring the saved setting |
| `--cooloff=<hours>` | Override the cool-off period |
| `--window-start=<HH:MM>` / `--window-end=<HH:MM>` | Override the update window |
| `--now=<ISO timestamp>` | Simulate the clock at a specific time |
| `--releases-file=<path>` | Use a local JSON releases array instead of fetching GitHub (offline) |
| `--skip-preflight` | Bypass the Docker/disk/queue pre-flight checks |

## Community & Resources

- **Discussions:** [GitHub Discussions](https://github.com/Srinivasan-78/cairn/discussions) - Questions, ideas, and help
- **Issues:** [GitHub Issues](https://github.com/Srinivasan-78/cairn/issues) - Bug reports and feature requests
- **FAQ:** [FAQ.md](FAQ.md) - Find answers to frequently asked questions
- **Community Add-Ons:** [admin/docs/community-add-ons.md](admin/docs/community-add-ons.md) - Third-party content packs
- **Upstream project:** [Project NOMAD](https://github.com/Crosstalk-Solutions/project-nomad) - The project Cairn is derived from

> Website, Discord, and hosted benchmark leaderboard belonged to the upstream project and are not part of Cairn.

## License

Cairn is licensed under the [Apache License 2.0](LICENSE).

## Helper Scripts
Once installed, Cairn has a few helper scripts should you ever need to troubleshoot issues or perform maintenance that can't be done through the Command Center. All of these scripts are found in Cairn's install directory, `/opt/cairn`

###

###### Start Script - Starts all installed project containers
```bash
sudo bash /opt/cairn/start_cairn.sh
```
###

###### Stop Script - Stops all installed project containers
```bash
sudo bash /opt/cairn/stop_cairn.sh
```
###

###### Update Script - Attempts to pull the latest images for the Command Center and its dependencies (i.e. mysql) and recreate the containers. Note: this *only* updates the Command Center containers. It does not update the installable application containers - that should be done through the Command Center UI
```bash
sudo bash /opt/cairn/update_cairn.sh
```

###### Uninstall Script - Need to start fresh? Use the uninstall script to make your life easy. Note: this cannot be undone!
```bash
curl -fsSL https://raw.githubusercontent.com/Srinivasan-78/cairn/refs/heads/main/install/uninstall_cairn.sh -o uninstall_cairn.sh && sudo bash uninstall_cairn.sh
```
