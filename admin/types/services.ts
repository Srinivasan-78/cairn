/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​‌‌​‌​​​‌‌‌​‌‌​​‌​‌​​‌‌​‌​‌​‌‌​​​​‌​‌​​​‌​​​‌​​​‌​​​‌​​‌​​​​‌‌​‌​‌‌​‌‌​‌‌‌‌​‌​‌​​‌​​‌​​​​​‌​‌‌​‌​​‌​‌​‌​​​‌​‌‌‌​​‌‌​‌​​‌‌​​​‌​​​​‌​​‌‌​​‌​​​‌​‌‌​‌​​​‌‌​​​​​​‌‌‌​​​​‌‌​‌‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.3Ge5aDDHkoRAiQsLBdZ08l
 */
import Service from '#models/service'

export type ServiceSlim = Pick<
  Service,
  | 'id'
  | 'service_name'
  | 'installed'
  | 'installation_status'
  | 'ui_location'
  | 'custom_url'
  | 'friendly_name'
  | 'description'
  | 'icon'
  | 'powered_by'
  | 'display_order'
  | 'container_image'
  | 'available_update_version'
  | 'auto_update_enabled'
  | 'is_custom'
  | 'is_user_modified'
  | 'is_deprecated'
  | 'category'
> & { status?: string }
