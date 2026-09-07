/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌‌‌‌‌​‌‌​‌​‌​​‌‌​​‌‌​​‌‌‌​​​‌​‌​‌‌​​​​‌‌‌​‌‌‌​‌​‌​​‌​​‌​‌​‌‌‌​‌‌​​​‌​​‌‌‌​​​​​​‌‌​​​​​​‌‌​‌‌​​‌‌‌​​​‌​‌‌‌​‌‌​​‌​‌​‌‌​​‌​‌‌​‌​​‌​​‌​​​​​‌‌​‌‌‌​‌‌​‌‌‌​​‌​‌​‌‌‌​​‌‌​‌​​​‌​​‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1._jfqXwRWbp06qvVZH7nW4I
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'installed_tiers'

  async up() {
    this.schema.createTable(this.tableName, (table) => {
      table.increments('id').primary()
      table.string('category_slug').notNullable().unique()
      table.string('tier_slug').notNullable()
      table.timestamp('created_at')
      table.timestamp('updated_at')
    })
  }

  async down() {
    this.schema.dropTable(this.tableName)
  }
}
