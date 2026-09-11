/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​‌‌​​‌​‌​‌‌‌​‌​‌​‌‌‌​‌‌‌​‌​‌​‌​‌‌​​​​‌​​​‌​‌​‌‌‌‌​‌​​‌​​​‌​‌​‌‌​​‌‌​​‌‌​‌​​​​‌​‌​​‌​​‌‌‌​​‌​​‌​​​​​‌​‌​​‌‌​‌​‌​​​​‌‌​‌‌‌​‌‌​​‌‌‌​​​​​​‌‌​‌​​​‌‌‌​‌​‌​​‌‌​​‌‌​‌‌‌​​‌‌​‌​‌​‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.fWWuXEzEfhRrAMCvp4u3sW
 */
import { defineConfig } from '@adonisjs/shield'

const shieldConfig = defineConfig({
  /**
   * Configure CSP policies for your app. Refer documentation
   * to learn more
   */
  csp: {
    enabled: false,
    directives: {},
    reportOnly: false,
  },

  /**
   * Configure CSRF protection options. Refer documentation
   * to learn more
   */
  csrf: {
    enabled: false, // TODO: Enable CSRF protection
    exceptRoutes: [],
    enableXsrfCookie: true,
    methods: ['POST', 'PUT', 'PATCH', 'DELETE'],
  },

  /**
   * Control how your website should be embedded inside
   * iFrames
   */
  xFrame: {
    enabled: true,
    action: 'DENY',
  },

  /**
   * Force browser to always use HTTPS
   */
  hsts: {
    enabled: false, // TODO: Enable HSTS in production
    maxAge: '180 days',
  },

  /**
   * Disable browsers from sniffing the content type of a
   * response and always rely on the "content-type" header.
   */
  contentTypeSniffing: {
    enabled: true,
  },
})

export default shieldConfig
