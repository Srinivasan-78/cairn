/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​​​​​‌​​‌​‌​​‌​​​​​‌​‌​​​​​‌​‌​​​‌‌‌​‌‌​‌‌​​​‌‌‌​‌​‌​‌​‌​​​‌​‌​‌‌​‌​​‌‌​‌‌​​​‌‌​​‌‌‌​‌‌​‌‌​‌​​‌‌​​‌​​​‌‌​​​​​‌​‌​​‌​​​‌​‌‌​‌​‌​‌​​​​​‌‌​​‌‌‌​​‌‌​‌​​​‌‌‌​​​​​​‌‌​‌​​​‌‌​‌​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.pJAAGluQZlgm20R-Pg4p4h
 */
import vine from '@vinejs/vine'

// Allow an empty/absent value so the user can clear their Cairn.md — AdonisJS
// converts empty request strings to null, so `optional()` (coerced to '' in the
// controller) is what lets a "clear" through. The cap keeps a single system
// prompt from growing unbounded.
export const updateCairnMdSchema = vine.compile(
  vine.object({
    content: vine.string().maxLength(100_000).optional(),
  })
)
