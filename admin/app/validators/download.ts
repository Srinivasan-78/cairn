/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌‌‌‌​‌‌​‌​​‌​‌‌​​​‌​​​‌‌​‌​​​​‌‌​‌​‌​‌‌​​‌​‌​​‌‌‌​​​​​‌‌​‌​‌​‌​​​​‌‌​‌​​‌​‌​​‌‌​‌‌​​​‌​​‌‌​​​‌​‌​‌‌​​‌‌​‌​​​​‌‌‌​‌​​​​‌‌​‌‌‌​‌​​‌‌‌​​‌​‌​​​​​‌​‌‌​​‌​‌​‌​‌‌​​‌‌​‌‌‌‌​‌‌​​​‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.Oib45e85CJlLVht7NPYVoc
 */
import vine from '@vinejs/vine'

export const downloadJobsByFiletypeSchema = vine.compile(
  vine.object({
    params: vine.object({
      filetype: vine.string(),
    }),
  })
)

export const modelNameSchema = vine.compile(
  vine.object({
    model: vine.string(),
  })
)
