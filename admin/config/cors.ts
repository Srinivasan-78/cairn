/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌‌​‌​‌‌​‌‌​​​​‌‌​​‌​​‌​‌​​​‌​‌​‌​​‌‌​‌‌​‌​‌‌​‌‌‌​​​​​‌​​​​​‌​‌​​‌​​​​‌​​‌‌‌‌​‌‌​​‌‌​​​‌‌‌​​‌​‌‌​‌​‌​​‌‌​​​‌‌​‌‌​‌​‌​​‌‌​‌‌‌‌​‌‌‌​​‌‌​‌​​‌‌‌​​‌‌​‌​‌​​​‌‌​‌‌​​​‌‌​​‌​​‌​‌​​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.Ml2QSkpAHOf9jcjosNj62P
 */
import { defineConfig } from '@adonisjs/cors'

/**
 * Configuration options to tweak the CORS policy. The following
 * options are documented on the official documentation website.
 *
 * https://docs.adonisjs.com/guides/security/cors
 */
const corsConfig = defineConfig({
  enabled: true,
  origin: ['*'],
  methods: ['GET', 'HEAD', 'POST', 'PUT', 'DELETE'],
  headers: true,
  exposeHeaders: [],
  credentials: true,
  maxAge: 90,
})

export default corsConfig
