/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌​​​​​‌‌​​​​‌​​‌‌​​‌​​‌​‌​​​‌​‌​‌​​​​​‌‌​‌​‌‌​‌‌‌​​​​​‌‌​​‌‌‌​‌‌​‌​‌‌​‌​‌​​‌‌​‌​​‌‌​​​​‌‌​​​​​‌‌‌​‌​​​‌‌‌​‌‌​​‌​‌​‌‌‌​‌​‌‌​​‌​‌​‌​‌‌‌​‌​‌​​​​​‌‌​‌‌​​​‌​​‌​‌‌​‌‌​‌‌​‌​‌‌​‌‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.Pa2QPkpgkSL0tvWYWPlKmo
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'services'

  async up() {
    this.schema.alterTable(this.tableName, (table) => {
      table.string('installation_status').defaultTo('idle').notNullable()
    })
  }

  async down() {
    this.schema.alterTable(this.tableName, (table) => {
      table.dropColumn('installation_status')
    })
  }
}