/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​‌​​​‌​​‌‌‌‌​​‌‌​‌‌​​‌​​​​‌‌​‌​​‌​​​​‌​‌​​​​​‌​‌‌‌‌‌​‌​‌‌​​​​‌‌​​‌​​​‌​​​‌‌​​‌‌‌​‌​​​‌​‌‌​​‌​‌​‌‌​​​​‌‌​‌​‌​​‌​‌​‌‌​​‌​‌​‌‌‌​‌‌​​‌‌‌​​‌‌​​‌‌​​‌‌‌​​​​‌​‌​‌‌‌​‌‌‌​​​​​‌‌​​‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.4O6CHP_XdFtYXjVWg38Wpg
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'kb_ingest_state'

  async up() {
    this.schema.alterTable(this.tableName, (table) => {
      table.string('collection').nullable().index()
    })
  }

  async down() {
    this.schema.alterTable(this.tableName, (table) => {
      table.dropColumn('collection')
    })
  }
}
