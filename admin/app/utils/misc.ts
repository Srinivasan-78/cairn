/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​‌​‌​‌​‌‌​‌​​‌‌‌​‌‌​​‌​​​‌‌​​‌​​​‌​​​‌​‌​​​​​‌‌​‌‌​‌​‌‌‌‌​​​​‌‌‌‌​​​​‌‌‌​‌​‌​‌​​‌​​​​‌​‌​​‌‌​‌‌‌​‌‌‌​‌‌​​‌​‌​‌​‌​​​‌​‌‌​​‌​​​‌​​​‌​​​‌‌​​​‌‌​​‌​‌‌​‌​‌​‌‌​​​​‌‌​‌​​​​‌‌​​‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.5ZvFDPmxxuHSweQdDc-Xhf
 */
export function formatSpeed(bytesPerSecond: number): string {
  if (bytesPerSecond < 1024) return `${bytesPerSecond.toFixed(0)} B/s`
  if (bytesPerSecond < 1024 * 1024) return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`
  return `${(bytesPerSecond / (1024 * 1024)).toFixed(1)} MB/s`
}

export function toTitleCase(str: string): string {
  return str
    .toLowerCase()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function parseBoolean(value: any): boolean {
  if (typeof value === 'boolean') return value
  if (typeof value === 'string') {
    const lower = value.toLowerCase()
    return lower === 'true' || lower === '1'
  }
  if (typeof value === 'number') {
    return value === 1
  }
  return false
}