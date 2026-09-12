/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌‌‌​​‌​‌​​‌‌​‌​‌​​​​​‌‌​‌​​‌​‌​​‌​​‌​‌​​​​‌​​​‌‌​​‌​​‌​​​​‌​​‌​‌​‌‌​​‌‌​‌​‌​​​‌‌​‌‌‌​‌​​‌‌​‌​‌‌‌‌​​​​‌​​‌​‌‌​‌‌‌​‌‌​​‌‌‌‌​‌​​‌​‌​‌​​​‌​​‌‌​​​‌‌‌​‌​‌​‌​​‌​‌‌​‌​​‌‌‌‌​‌‌‌‌​‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.NSPiIB2BVj7MxKvzTLuKOz
 */
import { DateTime } from 'luxon'
import { BaseModel, column, hasMany, SnakeCaseNamingStrategy } from '@adonisjs/lucid/orm'
import type { HasMany } from '@adonisjs/lucid/types/relations'
import ChatMessage from './chat_message.js'

export default class ChatSession extends BaseModel {
  static namingStrategy = new SnakeCaseNamingStrategy()

  @column({ isPrimary: true })
  declare id: number

  @column()
  declare title: string

  @column()
  declare model: string | null

  @hasMany(() => ChatMessage, {
    foreignKey: 'session_id',
    localKey: 'id',
  })
  declare messages: HasMany<typeof ChatMessage>

  @column.dateTime({ autoCreate: true })
  declare created_at: DateTime

  @column.dateTime({ autoCreate: true, autoUpdate: true })
  declare updated_at: DateTime
}