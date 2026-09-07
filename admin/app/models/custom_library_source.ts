/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​‌‌‌​‌​​‌​​‌​‌‌​‌‌‌​​‌‌​‌‌‌‌​‌​​‌​​​​‌​‌‌​​​​‌​​‌‌‌​​‌​​​​‌​​​‌‌‌​​‌​‌​​​‌​‌​‌‌‌​​​‌​‌‌​‌​‌‌​‌​‌‌‌‌‌​‌‌‌​​‌​​​‌​‌‌​‌​​‌‌​​‌‌​‌‌‌​​​​​‌​‌​​‌​​‌‌​​​‌‌​‌‌​‌‌‌​​‌‌‌​​​​​​‌‌​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.7InoHXNB9Eqk_r-3pRcnp4
 */
import { DateTime } from 'luxon'
import { BaseModel, column, SnakeCaseNamingStrategy } from '@adonisjs/lucid/orm'

export default class CustomLibrarySource extends BaseModel {
  static namingStrategy = new SnakeCaseNamingStrategy()

  @column({ isPrimary: true })
  declare id: number

  @column()
  declare name: string

  @column()
  declare base_url: string

  @column()
  declare is_default: boolean

  @column.dateTime({ autoCreate: true })
  declare created_at: DateTime

  @column.dateTime({ autoCreate: true, autoUpdate: true })
  declare updated_at: DateTime
}
