/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌​​​​‌​‌‌‌‌‌​‌​​​‌​‌​‌​‌‌​‌​​‌​​​​‌​​‌​‌​​‌​​‌​​​‌​‌​‌​‌‌​​‌​‌​‌​​​​​‌​​‌‌​​​‌‌​​‌​‌​‌​​​‌‌‌​‌​​​​​‌​‌​​​‌‌​​‌​‌‌​​‌​‌​​​‌​‌​​‌​‌‌​‌​‌​​​​‌​​‌‌‌​​​​​‌​​‌‌​​​‌‌‌​​‌‌​‌​​‌‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.H_EZBREYPLeGAFYE-BpLsO
 */
import vine from '@vinejs/vine'

export const createSessionSchema = vine.compile(
  vine.object({
    title: vine.string().trim().minLength(1).maxLength(200),
    model: vine.string().trim().optional(),
  })
)

export const updateSessionSchema = vine.compile(
  vine.object({
    title: vine.string().trim().minLength(1).maxLength(200).optional(),
    model: vine.string().trim().optional(),
  })
)

export const addMessageSchema = vine.compile(
  vine.object({
    role: vine.enum(['system', 'user', 'assistant'] as const),
    content: vine.string().trim().minLength(1),
  })
)