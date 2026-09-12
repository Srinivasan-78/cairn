/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​​​‌​​‌​‌‌​‌​‌‌​​​‌​​‌​‌​‌‌‌​‌​​​‌‌​​‌‌‌​​​‌​‌‌​‌‌‌‌​‌​​​‌‌‌​‌​‌‌​‌​​‌‌​‌‌​‌​‌​​​​​‌​‌​​​​‌‌​‌​‌‌​​​​​‌‌​​‌​​‌‌‌​​​‌​‌​‌​​​​​‌​​​‌‌‌​‌‌‌​‌‌​​​‌‌​‌‌‌​‌​‌​‌​​​‌‌​‌‌​​​‌‌​​​‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.q-bWFqoGZmACX2qPGv7Tlc
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'services'

  async up() {
    this.defer(async (db) => {
      await db
        .from(this.tableName)
        .where('service_name', 'cairn_kiwix_server')
        .whereRaw('`container_command` LIKE ?', ['%*.zim%'])
        .update({
          container_command: '--library /data/kiwix-library.xml --monitorLibrary --address=all',
        })
    })
  }

  async down() {
    this.defer(async (db) => {
      await db
        .from(this.tableName)
        .where('service_name', 'cairn_kiwix_server')
        .where('container_command', '--library /data/kiwix-library.xml --monitorLibrary --address=all')
        .update({
          container_command: '*.zim --address=all',
        })
    })
  }
}
