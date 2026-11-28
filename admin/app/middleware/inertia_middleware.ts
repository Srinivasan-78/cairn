import type { HttpContext } from '@adonisjs/core/http'
import type { NextFn } from '@adonisjs/core/types/http'
import BaseInertiaMiddleware from '@adonisjs/inertia/inertia_middleware'
import KVStore from '#models/kv_store'
import { SystemService } from '#services/system_service'

let _assistantNameCache: { value: string; expiresAt: number } | null = null

export function invalidateAssistantNameCache() {
  _assistantNameCache = null
}

export default class InertiaMiddleware extends BaseInertiaMiddleware {
  async handle(ctx: HttpContext, next: NextFn) {
    await this.init(ctx)
    const output = await next()
    this.dispose(ctx)
    return output
  }

  async share(_ctx: HttpContext) {
    return {
      appVersion: () => SystemService.getAppVersion(),
      environment: process.env.NODE_ENV || 'production',
      aiAssistantName: async () => {
        const now = Date.now()
        if (_assistantNameCache && now < _assistantNameCache.expiresAt) {
          return _assistantNameCache.value
        }
        const customName = await KVStore.getValue('ai.assistantCustomName')
        const value = customName && customName.trim() ? customName : 'AI Assistant'
        _assistantNameCache = { value, expiresAt: now + 60_000 }
        return value
      },
    }
  }
}
