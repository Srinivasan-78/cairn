/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​​​‌‌​‌‌‌​​​​​​‌‌​‌‌‌​‌‌‌​‌​​​‌‌​​​‌‌​​‌​‌‌​‌​‌‌‌‌​​‌​‌​​‌​‌‌​‌​‌​​‌​​​‌‌‌​​‌​‌‌‌​‌‌‌​‌‌​‌​‌​​‌‌‌‌​​​​‌‌‌‌​​​​​‌‌​‌‌​​‌​‌​​​​​‌​‌​​‌​​‌​​‌‌‌​​‌​‌​‌​‌​​‌‌​‌​‌​‌​‌​‌‌​​‌‌‌​​‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.Cp7tc-yKR9wjxx6PRNU5Vr
 */
import env from '#start/env'
import { defineConfig } from '@adonisjs/transmit'
import { redis } from '@adonisjs/transmit/transports'

export default defineConfig({
  pingInterval: '30s',
  transport: {
    driver: redis({
      host: env.get('REDIS_HOST'),
      port: env.get('REDIS_PORT'),
      db: env.get('REDIS_DB') ?? 0,
      keyPrefix: 'transmit:',
    })
  }
})