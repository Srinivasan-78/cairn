/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌​‌‌​‌​​​‌‌​​‌​‌‌​‌​​‌​​‌​​‌​‌​​‌‌‌​​‌‌‌​​​‌​‌​‌​‌​​​​‌‌​‌‌​​‌​​‌​​‌​‌​​​‌‌​​‌‌​​‌‌‌​‌‌‌​​‌‌​‌‌‌​‌​‌​‌​​‌‌​​​‌‌‌​​‌‌​‌‌​​‌​‌​‌​​‌‌‌​​​‌‌​‌‌​​‌‌​‌‌​​​‌​​​‌​​​​‌‌‌​​‌​‌​​​‌​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.kFZINqT6IFgsuLseN6lD9E
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'benchmark_results'

  async up() {
    this.schema.createTable(this.tableName, (table) => {
      table.increments('id')
      table.string('benchmark_id').unique().notNullable()
      table.enum('benchmark_type', ['full', 'system', 'ai']).notNullable()

      // Hardware information
      table.string('cpu_model').notNullable()
      table.integer('cpu_cores').notNullable()
      table.integer('cpu_threads').notNullable()
      table.bigInteger('ram_bytes').notNullable()
      table.enum('disk_type', ['ssd', 'hdd', 'nvme', 'unknown']).notNullable()
      table.string('gpu_model').nullable()

      // System benchmark scores
      table.float('cpu_score').notNullable()
      table.float('memory_score').notNullable()
      table.float('disk_read_score').notNullable()
      table.float('disk_write_score').notNullable()

      // AI benchmark scores (nullable for system-only benchmarks)
      table.float('ai_tokens_per_second').nullable()
      table.string('ai_model_used').nullable()
      table.float('ai_time_to_first_token').nullable()

      // Composite Cairn score (0-100)
      table.float('cairn_score').notNullable()

      // Repository submission tracking
      table.boolean('submitted_to_repository').defaultTo(false)
      table.timestamp('submitted_at').nullable()
      table.string('repository_id').nullable()

      table.timestamp('created_at')
      table.timestamp('updated_at')
    })
  }

  async down() {
    this.schema.dropTable(this.tableName)
  }
}
