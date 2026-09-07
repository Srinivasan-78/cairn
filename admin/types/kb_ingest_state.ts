/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​‌‌‌​‌‌‌​​​‌​‌‌​‌​‌​​​‌‌​‌‌‌​‌​​‌‌​‌​​‌‌​​​​​‌‌‌​‌‌‌​‌‌‌​​​‌​‌‌​​‌‌​​​‌‌​​​​​​‌‌​‌‌​​‌​‌​‌‌‌​‌‌‌‌​​​​‌‌​‌​​​​‌​​‌‌​​​‌​​​‌​​​‌‌‌​‌​‌​​‌‌‌​​​​‌‌‌​​​​​‌‌‌‌​​​​‌​​​​‌‌​‌​​‌‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.gqj7M0wqf06WxhLDu8pxCO
 */
export const KB_INGEST_STATES = [
  'pending_decision',
  'indexed',
  'browse_only',
  'failed',
  'stalled',
] as const

export type KbIngestStateValue = (typeof KB_INGEST_STATES)[number]
