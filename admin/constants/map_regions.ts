/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​​‌​​‌‌‌‌​​‌​​‌‌​‌‌​​‌​​​‌​​​‌‌‌​​​​​‌​‌​‌​​​‌​‌‌‌‌‌​‌​​​‌​​​‌​​‌‌​​​​‌‌‌​​‌​‌‌‌​‌‌​​‌​‌‌‌‌‌​‌‌​​‌​​​‌​​​​‌‌​‌​​​‌‌‌​​‌‌​​‌‌​‌​​‌‌​‌​​‌‌​​​‌​‌​​‌​​​​​‌‌​​‌‌​‌‌​​‌‌​​​‌‌​​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.ry6DpT_DL9v_dCG3M1H3f1
 */
export const PMTILES_BINARY_PATH = '/usr/local/bin/pmtiles'

// Clamp these so a user can't ask for nonsense that never extracts
export const EXTRACT_MIN_ZOOM = 0
export const EXTRACT_MAX_ZOOM = 15
export const EXTRACT_DEFAULT_MAX_ZOOM = 15

// Low-zoom global fallback extracted once during base-asset setup (~15 MB). Layered
// underneath regional extracts so the map isn't grey outside a region's polygon.
export const WORLD_BASEMAP_FILENAME = 'world.pmtiles'
export const WORLD_BASEMAP_MAX_ZOOM = 5
export const WORLD_BASEMAP_SOURCE_NAME = 'world'

export interface PmtilesExtractArgOptions {
  sourceUrl: string
  outputFilepath: string
  regionFilepath?: string
  maxzoom?: number
  dryRun?: boolean
  downloadThreads?: number
  overfetch?: number
}

export function buildPmtilesExtractArgs(opts: PmtilesExtractArgOptions): string[] {
  const args = ['extract', opts.sourceUrl, opts.outputFilepath]
  if (opts.regionFilepath) args.push(`--region=${opts.regionFilepath}`)
  if (typeof opts.maxzoom === 'number') args.push(`--maxzoom=${opts.maxzoom}`)
  if (opts.dryRun) args.push('--dry-run')
  if (typeof opts.downloadThreads === 'number') args.push(`--download-threads=${opts.downloadThreads}`)
  if (typeof opts.overfetch === 'number') args.push(`--overfetch=${opts.overfetch}`)
  return args
}
