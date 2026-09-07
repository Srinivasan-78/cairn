/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌‌​​​​‌‌​​‌‌​​‌​‌​‌‌​​​‌‌​‌​‌​​‌‌​​‌​​‌​​​​‌​​​‌‌​​‌‌​‌‌​​​‌‌​‌‌​‌‌​‌​‌‌​​‌‌‌​‌‌​​​‌‌​‌‌‌‌​​‌​‌​‌‌‌‌‌​‌​​‌‌​‌​‌​‌​‌​​​‌​​‌​‌​​‌‌​‌‌​‌​‌‌‌​​​‌​‌‌‌​‌​‌​‌​‌​​‌‌​‌​​‌‌​​​‌​‌‌‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.xfV52B3cmgcy_MTJmquSL_
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'services'

  async up() {
    this.schema.createTable(this.tableName, (table) => {
      table.increments('id')
      table.string('service_name').unique().notNullable()
      table.string('container_image').notNullable()
      table.string('container_command').nullable()
      table.json('container_config').nullable()
      table.boolean('installed').defaultTo(false)
      table.string('depends_on').nullable().references('service_name').inTable(this.tableName).onDelete('SET NULL')
      table.boolean('is_dependency_service').defaultTo(false)
      table.string('ui_location')
      table.json('metadata').nullable()
      table.timestamp('created_at')
      table.timestamp('updated_at')
    })
  }

  async down() {
    this.schema.dropTable(this.tableName)
  }
}