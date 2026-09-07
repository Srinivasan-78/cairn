/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌​‌‌‌​​‌‌​​‌​​​‌‌​​​‌​‌‌​‌‌​​​‌​‌​​​​​‌​‌‌​​​​‌​​‌‌‌‌​‌​​‌‌​​​‌‌‌​​​‌​​‌‌​​‌​​‌​​​‌‌‌​​‌‌​​‌‌​​‌‌​‌​‌​‌‌​​‌​‌​‌​‌‌​​​​‌‌​‌‌‌​​‌‌​​‌‌​​‌‌‌​‌‌‌​‌‌​‌‌‌‌​‌​​‌‌‌​​‌‌​​​‌​​‌​​‌‌​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.W21lPXOLq2G35eXnfwoNbM
 */
import { CollectionUpdateService } from '#services/collection_update_service'
import {
  assertNotPrivateUrl,
  applyContentUpdateValidator,
  applyAllContentUpdatesValidator,
} from '#validators/common'
import type { HttpContext } from '@adonisjs/core/http'

export default class CollectionUpdatesController {
  async checkForUpdates({}: HttpContext) {
    const service = new CollectionUpdateService()
    return await service.checkForUpdates()
  }

  async applyUpdate({ request }: HttpContext) {
    const update = await request.validateUsing(applyContentUpdateValidator)
    assertNotPrivateUrl(update.download_url)
    const service = new CollectionUpdateService()
    return await service.applyUpdate(update)
  }

  async applyAllUpdates({ request }: HttpContext) {
    const { updates } = await request.validateUsing(applyAllContentUpdatesValidator)
    for (const update of updates) {
      assertNotPrivateUrl(update.download_url)
    }
    const service = new CollectionUpdateService()
    return await service.applyAllUpdates(updates)
  }
}
