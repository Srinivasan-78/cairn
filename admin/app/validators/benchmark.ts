/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​​‌‌​‌​​​‌​​​‌‌​​​​‌​‌‌‌​‌‌‌​​‌​‌‌​‌​‌‌​‌​‌‌​‌‌‌​‌​‌​‌​‌​​‌​​​‌​‌‌​‌​​‌‌​​​​​​‌‌​​​‌​‌​‌‌​​‌​‌‌​​​‌‌​‌‌​​‌​‌​‌‌​‌​​​​‌​‌​‌‌‌​‌‌​​‌‌​​‌‌​​‌‌​​​‌‌​‌‌‌​‌‌​​‌​​​​‌‌​‌‌​​‌​​‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.sDaw-kuR-01YcehWff7d6I
 */
import vine from '@vinejs/vine'

export const runBenchmarkValidator = vine.compile(
  vine.object({
    benchmark_type: vine.enum(['full', 'system', 'ai']).optional(),
  })
)

export const submitBenchmarkValidator = vine.compile(
  vine.object({
    benchmark_id: vine.string().optional(),
  })
)
