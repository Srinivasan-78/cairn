/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​​​​‌​‌​‌​​​‌‌​​‌​‌​​‌‌​‌​​​​‌‌​​‌​​‌‌‌​‌‌‌​‌‌​‌‌​‌​‌​​​‌‌‌​‌‌‌​‌​​​‌‌‌‌​​​​‌​​‌‌‌​​‌‌‌​​​‌​‌‌​​‌​​​‌‌​​​​‌​‌‌​‌‌‌​​‌‌‌‌​​​​‌‌‌​​​​​‌​​​‌​​​‌‌​‌‌‌‌​‌​​​​‌​​‌‌‌​‌‌​​‌​​​​‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.0Te42wmGtxNqdanxpDoBvC
 */
import type { HttpContext } from '@adonisjs/core/http'
import type { NextFn } from '@adonisjs/core/types/http'

/**
 * Updating the "Accept" header to always accept "application/json" response
 * from the server. This will force the internals of the framework like
 * validator errors or auth errors to return a JSON response.
 */
export default class ForceJsonResponseMiddleware {
  async handle({ request }: HttpContext, next: NextFn) {
    const headers = request.headers()
    headers.accept = 'application/json'

    return next()
  }
}
