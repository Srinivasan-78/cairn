/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​‌​​‌‌‌‌​​‌​‌​​​‌‌‌​‌‌‌​‌​​​‌​‌​‌‌‌​​‌‌‌​​​​‌​‌‌​​‌​‌​​‌‌​‌​​‌‌​‌‌‌​‌‌​​​‌‌​‌​‌​‌​‌​​‌‌​​​​​​‌‌​​‌​​‌‌​​‌​‌​‌‌‌​​​​​​‌​‌‌​‌​‌​​‌​​‌​‌​‌​​​​​‌‌​​​​‌​‌‌​‌​‌​​​‌‌​​​‌​‌‌‌​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.2yGtW8YM7cU02ep-IPaj1t
 */
import { defineConfig } from 'vite'
import { getDirname } from '@adonisjs/core/helpers'
import inertia from '@adonisjs/inertia/client'
import react from '@vitejs/plugin-react'
import adonisjs from '@adonisjs/vite/client'
import tailwindcss from '@tailwindcss/vite'


export default defineConfig({
  plugins: [inertia({ ssr: { enabled: false } }), react(), tailwindcss(), adonisjs({ entrypoints: ['inertia/app/app.tsx'], reload: ['resources/views/**/*.edge'] })],

  /**
   * Define aliases for importing modules from
   * your frontend code
   */
  resolve: {
    alias: {
      '~/': `${getDirname(import.meta.url)}/inertia/`,
    },
  },
  server: {
    allowedHosts: true // This is for dev environments only. Can be overriden with `__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS` if needed.
  }
})
