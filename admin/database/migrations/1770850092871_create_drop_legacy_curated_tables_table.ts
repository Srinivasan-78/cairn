/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌​​‌​​‌‌​​‌​​​‌​​​‌‌​​‌‌‌​​​​​‌​​​​‌​​‌‌‌​​​‌​‌​‌‌​​​​‌​​​​​‌​‌‌​‌‌‌‌​​‌‌​​‌‌​‌​‌​‌​​​​‌‌​​‌‌​​‌‌‌​​​​‌​‌‌​‌​​‌​‌‌​​​​‌​‌‌‌‌‌​‌‌‌‌​​​​‌‌‌​​​‌​​‌‌​​​‌​‌‌​‌‌‌‌​‌‌​​‌‌​​‌‌​‌‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.RdFpBqXAo3T38ZX_xq1ofn
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  async up() {
    this.schema.dropTableIfExists('curated_collection_resources')
    this.schema.dropTableIfExists('curated_collections')
    this.schema.dropTableIfExists('zim_file_metadata')
  }

  async down() {
    // These tables are legacy and intentionally not recreated
  }
}
