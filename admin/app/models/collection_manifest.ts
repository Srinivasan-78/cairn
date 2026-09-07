/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​‌​‌​​‌‌‌​​‌​‌​​​‌​​​‌‌​‌​​‌​‌​‌‌​​​​​‌‌‌​​​​‌‌​‌‌‌‌​‌​​‌​​‌​‌‌‌​‌‌​​‌​‌​‌‌‌​‌​​​​‌​​‌​​​​‌​​‌‌​​​‌​​‌‌‌​‌‌​​​‌‌‌​​‌​‌​‌​‌​‌​‌​​‌‌​​​‌‌​‌​‌​​‌‌​‌​​‌​‌‌‌​‌​‌​‌​​‌​‌​​‌‌​‌​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.u9DiX8oIvWBBbv9ULjiuJh
 */
import { DateTime } from 'luxon'
import { BaseModel, column, SnakeCaseNamingStrategy } from '@adonisjs/lucid/orm'
import type { ManifestType } from '../../types/collections.js'

export default class CollectionManifest extends BaseModel {
  static namingStrategy = new SnakeCaseNamingStrategy()

  @column({ isPrimary: true })
  declare type: ManifestType

  @column()
  declare spec_version: string

  @column({
    consume: (value: string) => (typeof value === 'string' ? JSON.parse(value) : value),
    prepare: (value: any) => JSON.stringify(value),
  })
  declare spec_data: any

  @column.dateTime()
  declare fetched_at: DateTime
}
