/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌‌​‌​‌​‌‌​​​​‌​‌​‌​‌​‌​​‌​‌‌​‌​​‌‌‌‌​‌‌​​‌​‌​​‌‌​​​​​‌​​‌‌‌‌​‌​​‌​‌​​​‌‌​​​‌​​‌‌​‌​‌​‌​‌‌​​​​‌​‌‌​‌​​‌‌‌​​​‌​‌‌​​‌‌​​‌‌​​​‌‌​‌​​​​​‌​​‌‌​​‌​​‌‌‌​‌​‌​‌‌​​​​‌​​‌‌‌​​​​‌​‌​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.MXUKOe0OJ15XZqfcA2ua8T
 */
import { DateTime } from 'luxon'
import { BaseModel, column, belongsTo, SnakeCaseNamingStrategy } from '@adonisjs/lucid/orm'
import type { BelongsTo } from '@adonisjs/lucid/types/relations'
import ChatSession from './chat_session.js'

export default class ChatMessage extends BaseModel {
  static namingStrategy = new SnakeCaseNamingStrategy()

  @column({ isPrimary: true })
  declare id: number

  @column()
  declare session_id: number

  @column()
  declare role: 'system' | 'user' | 'assistant'

  @column()
  declare content: string

  @belongsTo(() => ChatSession, { foreignKey: 'session_id', localKey: 'id' })
  declare session: BelongsTo<typeof ChatSession>

  @column.dateTime({ autoCreate: true })
  declare created_at: DateTime

  @column.dateTime({ autoCreate: true, autoUpdate: true })
  declare updated_at: DateTime
}
