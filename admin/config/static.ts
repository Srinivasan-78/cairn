/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌‌​​​​​‌‌​‌‌​​‌‌​​​‌‌​‌​‌‌​​‌​‌‌​‌‌​‌​‌‌‌​​​‌​‌​​​​​‌​‌​‌‌​​​​‌​​‌‌‌​​‌‌‌​​‌‌​‌‌‌​‌‌​​‌‌​​​​‌​​‌‌​‌‌​​‌‌‌‌​​​​‌​‌‌‌‌‌​‌​‌​‌‌‌​‌‌​‌‌‌‌​‌‌​‌‌‌​​‌‌​​​‌‌​‌​​​​‌‌​‌​‌​​‌‌​‌​​‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.x6cYmqAXNsva6x_WoncCSI
 */
import { defineConfig } from '@adonisjs/static'

/**
 * Configuration options to tweak the static files middleware.
 * The complete set of options are documented on the
 * official documentation website.
 *
 * https://docs.adonisjs.com/guides/static-assets
 */
const staticServerConfig = defineConfig({
  enabled: true,
  etag: true,
  lastModified: true,
  dotFiles: 'ignore',
  acceptRanges: true,
})

export default staticServerConfig
