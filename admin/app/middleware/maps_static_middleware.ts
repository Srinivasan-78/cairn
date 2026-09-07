/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​‌​‌​​‌‌​​​‌​‌​‌‌​​‌​‌​​‌​​‌​‌​​‌‌‌‌​‌​​​​​‌​‌‌‌​​‌​​‌‌​‌​‌‌​‌‌​​‌‌‌​‌‌​‌‌‌‌​​‌‌‌​​​​​‌‌‌​​‌​‌‌​‌​‌‌​​‌‌​‌​​​‌​‌‌​​​​‌​‌​​​‌​‌‌​‌‌​​​‌‌​‌‌‌​​‌‌​​‌​‌​‌​​​‌‌‌​‌​​​‌‌​​‌‌‌​​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.51YIOArkgo89k4XQlneGFq
 */
import type { HttpContext } from '@adonisjs/core/http'
import type { NextFn } from '@adonisjs/core/types/http'
import StaticMiddleware from '@adonisjs/static/static_middleware'
import { AssetsConfig } from '@adonisjs/static/types'

/**
 * See #providers/map_static_provider.ts for explanation
 * of why this middleware exists.
 */
export default class MapsStaticMiddleware {
  constructor(
    private path: string,
    private config: AssetsConfig
  ) {}

  async handle(ctx: HttpContext, next: NextFn) {
    const staticMiddleware = new StaticMiddleware(this.path, this.config)
    return staticMiddleware.handle(ctx, next)
  }
}
