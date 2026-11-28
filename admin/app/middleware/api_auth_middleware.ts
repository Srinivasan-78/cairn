import type { HttpContext } from '@adonisjs/core/http'
import type { NextFn } from '@adonisjs/core/types/http'
import { timingSafeEqual } from 'node:crypto'

/**
 * Optional bearer-token gate and cross-site Origin guard for /api/* routes.
 *
 * - When `CAIRN_API_TOKEN` is set in the environment, all `/api/*` requests
 *   (except `/api/health`) must present a matching `Authorization: Bearer <token>`.
 * - For state-changing requests (`POST`, `PUT`, `PATCH`, `DELETE`), if a browser
 *   `Origin` header is present it must match the request `Host` (or `URL` env),
 *   preventing cross-site CSRF even when sessions are disabled.
 */
export default class ApiAuthMiddleware {
  async handle(ctx: HttpContext, next: NextFn) {
    const { request, response } = ctx
    const method = request.method().toUpperCase()

    // Cross-site Origin check on state-changing requests
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const origin = request.header('origin')
      if (origin) {
        try {
          const originHost = new URL(origin).host
          const requestHost = request.header('host')
          const configuredUrl = process.env.URL ? new URL(process.env.URL).host : null
          if (originHost !== requestHost && originHost !== configuredUrl) {
            return response.forbidden({ message: 'Cross-origin request rejected' })
          }
        } catch {
          return response.forbidden({ message: 'Invalid Origin header' })
        }
      }
    }

    const expectedToken = process.env.CAIRN_API_TOKEN
    if (expectedToken && request.url().startsWith('/api/') && request.url() !== '/api/health') {
      const authHeader = request.header('authorization') || ''
      const match = authHeader.match(/^Bearer\s+(.+)$/i)
      const provided = match?.[1] ?? ''
      const expectedBuf = Buffer.from(expectedToken, 'utf8')
      const providedBuf = Buffer.from(provided, 'utf8')
      if (
        expectedBuf.length === 0 ||
        providedBuf.length !== expectedBuf.length ||
        !timingSafeEqual(providedBuf, expectedBuf)
      ) {
        return response.unauthorized({ message: 'Unauthorized' })
      }
    }

    return next()
  }
}
