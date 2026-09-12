/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌​‌​​​‌​​‌​‌​​‌‌​​​‌​​‌​​‌​​‌​‌​‌​​​​​‌​‌​​‌‌​‌‌​‌​‌​​‌‌​‌​‌‌​​‌‌‌​​​​‌​​‌‌‌​​‌​‌​​​‌​‌‌‌​‌‌​​‌‌​​‌‌​​‌​​‌‌​‌​​‌​‌‌​‌​​‌‌​‌​​​‌​​‌‌‌​​‌‌​​‌​‌​​‌‌‌​​​​​‌‌​​‌​​‌​​‌‌‌‌​‌​​‌​‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.TJbIPSjk8NQvfM-4Ne82OJ
 */
import { BaseSchema } from '@adonisjs/lucid/schema'
import { SERVICE_NAMES } from '../../constants/service_names.js'

export default class extends BaseSchema {
  protected tableName = 'services'

  async up() {
    // Sunset the Meshtastic Daemon catalog entry. It was removed from the seeder's DEFAULT_SERVICES
    // because it can't work without hands-on setup (the user's radio MAC address, etc.), so leaving
    // the card in the catalog only offers a broken install. The seeder is additive + sync-existing
    // and never deletes, so every deployment seeded while it was in the catalog (all early-access
    // boxes) keeps an orphaned `cairn_meshtasticd` row and still shows the non-functional card.
    // Mirror the legacy-Kolibri sunset; the `is_deprecated` column already exists from that migration.
    this.defer(async (db) => {
      // Never installed → just an orphaned catalog row; drop it outright so the card disappears.
      await db
        .from(this.tableName)
        .where('service_name', SERVICE_NAMES.MESHTASTICD)
        .where('installed', false)
        .delete()

      // Currently installed (rare) → keep the row so it stays Cairn's handle to stop/uninstall the
      // container, but flag it deprecated: it drops out of the catalog (see SystemService.getServices)
      // and shows a "Legacy" badge. Honors the "we don't remove pre-installed apps" policy.
      await db
        .from(this.tableName)
        .where('service_name', SERVICE_NAMES.MESHTASTICD)
        .where('installed', true)
        .update({ is_deprecated: true })
    })
  }

  async down() {
    // The orphaned-row deletion is a one-way data change and is not restored here. The is_deprecated
    // column is owned by the legacy-Kolibri migration, so there is nothing schema-level to revert.
  }
}
