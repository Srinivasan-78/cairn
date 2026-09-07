/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌​‌‌​‌​​​‌​​​‌​‌​​​‌​‌​​‌​​‌​​‌‌​​​‌​‌​‌​​‌​​‌​​​​‌​​​‌‌​​‌​​‌​​​​‌‌​‌​‌‌​​​​‌‌​‌‌​‌​​‌‌​​​‌​‌​‌‌​​‌​‌​​‌‌‌​​‌‌​‌‌‌‌​‌​​‌​‌‌​‌‌‌​​​​​‌​‌​‌​‌​​‌​‌‌​‌​‌‌​​​‌​​​‌‌​​‌​​‌​​​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.kDQI1RB2CXm1YNoKpU-b2D
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'drug_labels'

  async up() {
    await this.db.rawQuery(
      'ALTER TABLE drug_labels MODIFY COLUMN ingested_at timestamp NOT NULL ' +
        'DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
    )
  }

  async down() {
    await this.db.rawQuery('ALTER TABLE drug_labels MODIFY COLUMN ingested_at timestamp NOT NULL')
  }
}
