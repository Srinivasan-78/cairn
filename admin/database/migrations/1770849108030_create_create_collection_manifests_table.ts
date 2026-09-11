/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​‌​​​‌‌​​​​​‌​‌​​​​​‌‌​​‌​‌​​‌‌​‌​​​‌​‌​​‌‌​‌‌​‌​‌‌​‌​‌​‌​​​‌​‌​​​‌​‌​​​‌​‌​‌​​‌​​‌​‌‌​‌​‌​​‌​‌​‌​​​‌‌‌​​​‌​​‌‌‌​​‌​‌‌‌‌​​‌​‌​‌​‌​​​‌‌​​‌‌​​​‌‌​‌‌‌​‌‌​‌​‌‌​‌​‌​‌‌‌​‌​‌​‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.20Pe4SkTQEIjTq9yTf7kWW
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'collection_manifests'

  async up() {
    this.schema.createTable(this.tableName, (table) => {
      table.string('type').primary() // 'zim_categories' | 'maps' | 'wikipedia'
      table.string('spec_version').notNullable()
      table.json('spec_data').notNullable()
      table.timestamp('fetched_at').notNullable()
    })
  }

  async down() {
    this.schema.dropTable(this.tableName)
  }
}
