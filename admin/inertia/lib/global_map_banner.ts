/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​‌‌‌​‌‌​​‌‌​​‌‌​‌‌​‌​‌​‌​​​​​‌‌​​​​‌​‌‌‌‌​​‌​‌​‌​​​​​‌​‌​‌​​​‌​​‌‌‌​​​‌‌‌​​‌​‌​​​‌‌‌​‌​​‌​‌​​‌‌​​​‌‌​‌‌‌​‌‌​​‌​‌​​‌​​‌‌​‌​‌‌​​‌‌​‌​‌​‌‌​‌​‌‌​‌​​​‌​‌​​‌‌​​​‌​‌​​‌​‌​​‌‌​​‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.7fmPayPTN9GJcvRk5kE1Jf
 */
export function hasDownloadedGlobalMap(
  globalMapKey: string | null | undefined,
  storedMapFiles: Array<{ name: string }>
): boolean {
  if (!globalMapKey) {
    return false
  }

  return storedMapFiles.some((file) => file.name === globalMapKey || /^\d{8}\.pmtiles$/.test(file.name))
}
