/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​​‌​​​‌‌​​​‌​​‌‌‌​​‌​‌‌​​‌‌​​​‌‌​​​​​‌​​​‌​‌​‌‌‌​​‌‌​‌‌‌​‌​‌​‌‌‌‌​‌​​‌​​‌​‌‌​​‌‌​​‌‌​‌‌​​‌​​​‌‌‌​​‌‌​‌‌​‌​‌‌​‌​​‌‌​‌​​‌‌​​​​​‌‌‌​​‌​​‌‌​​‌​​​‌​‌‌​‌​​‌​‌​​‌​​‌​​‌​‌‌​‌​​‌‌​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.r19f0EsuzK3dskM0rdZRKM
 */
export type BaseStylesFile = {
  version: number
  sources: {
    [key: string]: MapSource
  }
  layers: MapLayer[]
  sprite: string
  glyphs: string
}

export type MapSource = {
  type: 'vector' | 'raster' | 'raster-dem' | 'geojson' | 'image' | 'video'
  attribution?: string
  url: string
}

export type MapLayer = {
  'id': string
  'type': string
  'source'?: string
  'source-layer'?: string
  [key: string]: any
}

/** ISO 3166-1 alpha-2 country code (e.g. "DE", "FR", "US"). */
export type CountryCode = string

export type Country = {
  code: CountryCode
  code3: string
  name: string
  continent: string
  subregion: string
  population: number
}

export type CountryGroup = {
  id: string
  name: string
  description: string
  countries: CountryCode[]
}

export type MapExtractRequest = {
  countries: CountryCode[]
  maxzoom?: number
}

export type MapExtractPreflight = {
  tiles: number
  bytes: number
  source: {
    url: string
    date: string
    key: string
  }
}
