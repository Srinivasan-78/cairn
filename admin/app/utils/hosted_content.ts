/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌​​​​‌​​‌​‌​​‌​‌​‌​​​‌​​‌​​​​‌​‌​‌​‌​​‌‌​​‌​​​‌‌​​​‌​‌‌​‌​​​​‌‌​​‌​​​‌‌​‌​​​​‌‌‌​​​​​‌‌​​‌‌‌​‌​‌​‌‌​​‌​‌​‌​​​‌‌‌‌​​​​‌‌‌​​‌​​‌‌​​‌​​​‌‌​​‌​‌​‌​​​​‌​​‌​​‌​​​​‌​‌​‌‌​​‌​​‌‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.HJTHU21hdhpgVTxrdeBHVN
 */
import type { SpecResource } from '../../types/collections.js'

/**
 * Pure predicate for "is this a resource we host behind the entitlement Worker?"
 *
 * Deliberately kept free of any `#start/env` import. `zim_download_resolution` is
 * a pure, unit-tested module, and importing the env-reading side of this (see
 * hosted_content_auth.ts) would trigger env validation at module load and break
 * those tests outside a configured app context.
 */

/** The only gating scheme we support today. See SpecResource.auth. */
export const CAIRN_APP_KEY_AUTH = 'cairn_app_key' as const

export function isGatedResource(resource: Pick<SpecResource, 'auth'>): boolean {
  return resource.auth === CAIRN_APP_KEY_AUTH
}
