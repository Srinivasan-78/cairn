/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​‌​‌​‌‌​​​‌‌​​‌‌​‌​​​​‌‌​‌‌​​‌‌‌‌​​​​​‌‌​‌‌​​‌​‌‌​‌​​‌​‌​​‌‌​​‌‌​‌​​​‌​​‌‌‌‌​‌‌​‌‌‌​​‌​​‌‌​‌​‌‌‌​‌​​​‌‌​‌‌​​​​‌‌‌​​​​​‌‌​‌​​​​‌‌​​​​​‌‌​‌​​​​​‌‌‌​​‌​‌‌‌‌​​​​‌​​‌​‌​​​‌‌​‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.uc46x6ZS4OnMtl840h9xJ6
 */
import { Logger } from '@adonisjs/core/logger'
import { HttpContext } from '@adonisjs/core/http'
import { NextFn } from '@adonisjs/core/types/http'

/**
 * The container bindings middleware binds classes to their request
 * specific value using the container resolver.
 *
 * - We bind "HttpContext" class to the "ctx" object
 * - And bind "Logger" class to the "ctx.logger" object
 */
export default class ContainerBindingsMiddleware {
  handle(ctx: HttpContext, next: NextFn) {
    ctx.containerResolver.bindValue(HttpContext, ctx)
    ctx.containerResolver.bindValue(Logger, ctx.logger)

    return next()
  }
}
