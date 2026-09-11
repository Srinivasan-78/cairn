/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​‌​‌​‌‌‌​​‌​​‌‌‌​​​‌​‌‌​​‌‌‌​‌​‌​​‌‌​‌‌‌​​​‌​​‌‌​​​​​‌​​‌​‌​​‌​​‌​​​​‌​​‌​​‌​​‌‌​​‌‌​‌‌‌​‌​‌​‌‌‌​‌‌‌​​‌‌​‌​​​​‌‌​‌​‌​‌‌‌​‌‌‌​‌​​​​​‌​​‌‌​​‌‌​‌​‌​‌​‌​​‌‌‌​​‌​‌​​‌​‌‌​‌‌​‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.erqgSq0JHI3uw45wA3U9Ki
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'curated_collection_resources'

  async up() {
    this.schema.alterTable(this.tableName, (table) => {
      table.unique(['curated_collection_slug', 'url'], {
        indexName: 'curated_collection_resources_unique',
      })
    })
  }

  async down() {
    this.schema.alterTable(this.tableName, (table) => {
      table.dropUnique(['curated_collection_slug', 'url'], 'curated_collection_resources_unique')
    })
  }
}