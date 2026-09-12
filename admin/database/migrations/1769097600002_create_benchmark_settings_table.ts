/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​​‌‌​‌​​‌​‌​​‌‌‌‌​‌​​‌‌‌​​​‌​‌​‌​‌​‌​‌​‌‌​​‌​‌‌‌​​‌‌​‌​​‌‌​‌​‌​‌​‌​​​‌​‌​‌​​​‌​​​‌‌​​‌​‌​​​​​‌​​​‌​​​‌‌‌​​‌​​‌​‌‌​​‌​‌‌‌​‌‌​​‌‌​‌‌​​​‌​‌‌‌‌‌​​‌‌​​​​​​‌‌​​​​​‌​​‌‌​​​‌‌​​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.sJzqUYsMTTFPDrYvl_00Ld
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'benchmark_settings'

  async up() {
    this.schema.createTable(this.tableName, (table) => {
      table.increments('id')
      table.string('key').unique().notNullable()
      table.text('value').nullable()
      table.timestamp('created_at')
      table.timestamp('updated_at')
    })
  }

  async down() {
    this.schema.dropTable(this.tableName)
  }
}
