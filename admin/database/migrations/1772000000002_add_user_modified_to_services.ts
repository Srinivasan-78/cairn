/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​‌​‌​‌‌​​‌​​​‌‌‌​​​​​‌‌​​‌​‌​‌​‌‌​‌​​‌​​​‌‌​​‌​​​‌​‌​‌‌​​‌‌‌​‌​​‌‌​​​‌​‌‌​‌​​​‌​‌‌​‌​‌‌​‌​‌​​‌​​​​‌‌​‌‌​‌​‌‌​‌​‌‌​​‌​‌​​‌‌​‌​‌​​‌​‌​​‌​‌‌​‌​​​‌‌​‌‌‌​‌​​‌​​​​‌​​‌‌​‌​‌​​‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.udpeZFEgLZ-jCkYMJZ7HMI
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'services'

  async up() {
    this.schema.alterTable(this.tableName, (table) => {
      // Set when a user edits a curated (non-custom) app. Tells the seeder to stop
      // overwriting that service's container_config on subsequent runs, so the user's
      // customizations (e.g. a changed port) survive reboots and upgrades.
      table.boolean('is_user_modified').notNullable().defaultTo(false)
    })
  }

  async down() {
    this.schema.alterTable(this.tableName, (table) => {
      table.dropColumn('is_user_modified')
    })
  }
}
