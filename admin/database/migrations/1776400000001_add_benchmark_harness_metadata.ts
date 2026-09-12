/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌‌​‌​‌‌‌​‌​‌​‌​​‌​‌‌​‌​‌‌​​‌​‌‌‌​​‌‌​‌‌‌​​‌‌​‌​​‌‌​​​‌‌​​​​‌​‌​​‌‌​‌​‌​​​​​‌​‌‌​‌‌‌‌​‌‌‌‌​​‌​‌​‌​‌​‌​‌​‌​‌​​​‌​‌​​‌​​‌​​‌‌​‌​‌​‌​‌​‌​‌​​​‌​‌​‌​​​​​‌​‌​​​​‌‌​‌‌​‌‌‌​​‌​‌‌​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.MuKYssLaMAoyUTRMUEACnX
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'benchmark_results'

  async up() {
    this.schema.alterTable(this.tableName, (table) => {
      // Forensic harness metadata (Score v2 Phase 1): which sysbench image digest produced the
      // system scores, and which Ollama version served the AI benchmark. Both nullable —
      // pre-existing rows and runs without AI simply leave them empty.
      table.string('sysbench_digest').nullable()
      table.string('ollama_version').nullable()
    })
  }

  async down() {
    this.schema.alterTable(this.tableName, (table) => {
      table.dropColumn('sysbench_digest')
      table.dropColumn('ollama_version')
    })
  }
}
