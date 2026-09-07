/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌​‌‌​​‌‌​‌‌​​​​‌‌​​​‌​‌‌​​​‌‌​​‌‌​‌​‌​‌‌‌​​​‌​‌‌​‌​​​​‌‌​‌​‌‌​‌​​‌‌​​​‌​​‌‌‌​​‌​​‌​​‌​‌​‌‌​‌​​​‌‌​‌​‌​​‌‌‌​​​​‌​​​‌​‌​‌​‌‌‌‌‌​‌‌​​‌​​​​‌‌​‌​​​‌​‌​​​​​​‌‌‌​​‌​‌​‌​​​​​‌​​‌‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.Vl1c5qhkLNIZ58E_d4P9PN
 */
import { SystemService } from '#services/system_service'
import { inject } from '@adonisjs/core'
import type { HttpContext } from '@adonisjs/core/http'

@inject()
export default class SupplyDepotController {
  constructor(private systemService: SystemService) {}

  async index({ inertia }: HttpContext) {
    const services = await this.systemService.getServices({ installedOnly: false })
    return inertia.render('supply-depot', { system: { services } })
  }
}
