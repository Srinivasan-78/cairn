/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​‌‌​​‌​​‌‌​‌​‌​​‌​‌​​‌‌‌​​​​​‌‌‌​​​​​‌​‌​‌​‌​‌​​‌​​​​‌​​‌​‌‌​‌‌​‌‌​‌​‌‌​​‌‌​​‌​​‌‌​​​‌‌​‌​‌​​‌‌‌​​​​​‌‌‌‌​​​​‌‌​​‌​‌​‌​‌​‌‌​​‌‌‌​​‌‌​‌‌‌‌​‌​​‌​​​​‌‌​‌​‌​​‌‌​‌​‌​‌​‌​‌​‌​​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.6MJppUHKmfLjpxeVszCSUP
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'services'

  async up() {
    this.schema.alterTable(this.tableName, (table) => {
      table.boolean('is_custom').notNullable().defaultTo(false)
      table.string('category').nullable()
    })

    // Backfill categories for existing curated services
    this.defer(async (db) => {
      const updates: Array<{ service_name: string; category: string }> = [
        { service_name: 'cairn_kiwix_server', category: 'education' },
        { service_name: 'cairn_kolibri', category: 'education' },
        { service_name: 'cairn_ollama', category: 'ai' },
        { service_name: 'cairn_cyberchef', category: 'utility' },
        { service_name: 'cairn_flatnotes', category: 'productivity' },
      ]

      for (const { service_name, category } of updates) {
        await db.from('services').where('service_name', service_name).update({ category })
      }
    })
  }

  async down() {
    this.schema.alterTable(this.tableName, (table) => {
      table.dropColumn('is_custom')
      table.dropColumn('category')
    })
  }
}
