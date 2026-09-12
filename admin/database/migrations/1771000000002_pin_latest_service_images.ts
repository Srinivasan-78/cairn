/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌‌‌​​​‌‌​​​‌​‌‌​‌‌‌‌​‌​​‌​​​​‌‌‌‌​‌​​‌‌​​​‌​​‌‌​‌​​​​​‌‌​​‌​​​‌​‌‌​‌​‌‌​‌‌‌‌​‌‌‌​‌​‌​‌​​​‌​​​‌​​​​‌​​​‌‌​​‌‌​‌‌‌‌​​​​‌‌​​​‌​​‌​​​‌​​​‌​‌​​‌​​‌‌‌​​​​​‌​‌​​​​​‌‌​​‌​‌​​‌‌‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.N1oHzbh2-ouDB3xbDRpPe9
 */
import { BaseSchema } from '@adonisjs/lucid/schema'

export default class extends BaseSchema {
  protected tableName = 'services'

  async up() {
    this.defer(async (db) => {
      // Pin :latest images to specific versions
      await db
        .from(this.tableName)
        .where('container_image', 'ghcr.io/gchq/cyberchef:latest')
        .update({ container_image: 'ghcr.io/gchq/cyberchef:10.19.4' })

      await db
        .from(this.tableName)
        .where('container_image', 'dullage/flatnotes:latest')
        .update({ container_image: 'dullage/flatnotes:v5.5.4' })

      await db
        .from(this.tableName)
        .where('container_image', 'treehouses/kolibri:latest')
        .update({ container_image: 'treehouses/kolibri:0.12.8' })

      // Populate source_repo for services whose images lack the OCI source label
      const sourceRepos: Record<string, string> = {
        cairn_kiwix_server: 'https://github.com/kiwix/kiwix-tools',
        cairn_ollama: 'https://github.com/ollama/ollama',
        cairn_qdrant: 'https://github.com/qdrant/qdrant',
        cairn_cyberchef: 'https://github.com/gchq/CyberChef',
        cairn_flatnotes: 'https://github.com/dullage/flatnotes',
        cairn_kolibri: 'https://github.com/learningequality/kolibri',
      }

      for (const [serviceName, repoUrl] of Object.entries(sourceRepos)) {
        await db
          .from(this.tableName)
          .where('service_name', serviceName)
          .update({ source_repo: repoUrl })
      }
    })
  }

  async down() {
    this.defer(async (db) => {
      await db
        .from(this.tableName)
        .where('container_image', 'ghcr.io/gchq/cyberchef:10.19.4')
        .update({ container_image: 'ghcr.io/gchq/cyberchef:latest' })

      await db
        .from(this.tableName)
        .where('container_image', 'dullage/flatnotes:v5.5.4')
        .update({ container_image: 'dullage/flatnotes:latest' })

      await db
        .from(this.tableName)
        .where('container_image', 'treehouses/kolibri:0.12.8')
        .update({ container_image: 'treehouses/kolibri:latest' })
    })
  }
}
