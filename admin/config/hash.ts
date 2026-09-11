/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​‌​​‌‌‌​‌‌‌​‌​​‌‌​‌​‌‌​​‌​​​‌​​​‌​‌​‌‌‌​​​‌​‌​​‌‌‌‌​‌‌​​‌​​​‌​‌‌​​‌​​‌‌​​​​​‌​​​​‌​​‌​‌​​‌​​‌‌‌​​‌‌​​‌‌‌​​‌​‌‌​​​‌‌​‌‌​​‌​‌​‌​‌‌​‌​​‌‌​​‌​‌​‌‌‌​‌‌​​​‌‌​​‌‌​‌‌‌​‌‌​​‌​​‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.2wMdEqOdY0BRs9ceZev3vI
 */
import { defineConfig, drivers } from '@adonisjs/core/hash'

const hashConfig = defineConfig({
  default: 'scrypt',

  list: {
    scrypt: drivers.scrypt({
      cost: 16384,
      blockSize: 8,
      parallelization: 1,
      maxMemory: 33554432,
    }),
  },
})

export default hashConfig

/**
 * Inferring types for the list of hashers you have configured
 * in your application.
 */
declare module '@adonisjs/core/types' {
  export interface HashersList extends InferHashers<typeof hashConfig> {}
}
