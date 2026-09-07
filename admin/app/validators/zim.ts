/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​​‌​​​‌​​‌‌​​​​‌​‌‌​‌​​‌‌​​‌​​‌​​‌​​​​​‌‌​​​‌​‌​‌‌​​‌​‌​​​​‌​​‌‌​‌​‌​​​‌‌​‌​​​‌​​​‌‌‌​‌​​​‌‌‌​​‌‌​‌‌‌​​‌‌‌​​‌​‌​​​‌​​​‌‌​​‌​​​‌​​‌‌​‌​​‌‌‌​​‌​‌‌​‌‌​‌​‌‌​​​‌‌​​‌‌‌​​​​‌​‌‌‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.DL-2H1YBj4GG79DdM9mc8_
 */
import vine from '@vinejs/vine'

export const listRemoteZimValidator = vine.compile(
  vine.object({
    start: vine.number().min(0).optional(),
    count: vine.number().min(1).max(100).optional(),
    query: vine.string().optional(),
  })
)

export const addCustomLibraryValidator = vine.compile(
  vine.object({
    name: vine.string().trim().minLength(1).maxLength(100),
    base_url: vine
      .string()
      .url({ require_tld: false })
      .trim(),
  })
)

export const browseLibraryValidator = vine.compile(
  vine.object({
    url: vine
      .string()
      .url({ require_tld: false })
      .trim(),
  })
)

export const idParamValidator = vine.compile(
  vine.object({
    params: vine.object({
      id: vine.number(),
    }),
  })
)
