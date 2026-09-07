/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​​​​​‌​​‌‌‌‌​‌​‌‌​‌​​‌​​​‌‌‌​‌‌‌​‌​‌​‌‌‌​​​‌​‌​‌​‌​​​‌​​​‌‌‌​‌‌‌​​​‌​‌‌​‌​​​​‌‌​​‌​​​‌‌​​‌​‌​​‌‌​​​‌​‌‌‌​​​‌​‌‌​‌‌‌​​‌​​​‌​​​‌​​‌​‌‌​​‌‌​‌‌​​‌​​​​‌‌​‌‌‌​​‌​​‌​‌‌‌‌‌​‌‌‌​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.pOZGuqTGqhde1qnDK6Cr_t
 */
import vine from '@vinejs/vine'

export const getJobStatusSchema = vine.compile(
  vine.object({
    filePath: vine.string(),
  })
)

export const deleteFileSchema = vine.compile(
  vine.object({
    source: vine.string(),
  })
)

export const embedFileSchema = vine.compile(
  vine.object({
    source: vine.string().minLength(1),
    force: vine.boolean().optional(),
  })
)

export const fileSourceSchema = vine.compile(
  vine.object({
    source: vine.string().minLength(1),
  })
)

export const estimateBatchSchema = vine.compile(
  vine.object({
    files: vine
      .array(
        vine.object({
          filename: vine.string().minLength(1).maxLength(255),
          sizeBytes: vine.number().min(0),
        })
      )
      .minLength(1)
      .maxLength(500),
  })
)
