/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​‌‌‌​‌‌​​‌‌‌​‌​​‌​‌‌​​‌‌​‌‌‌​‌​‌​‌‌​​‌‌‌​​​​​‌‌‌​‌​‌​‌​‌​‌​​​‌‌‌‌​​‌​‌‌​​‌​​​‌‌‌​​​​​‌‌​​​‌​​‌​​​‌​‌​‌​‌​‌‌​​​‌‌​​‌​​‌​​​‌​​​‌‌​‌‌‌​​‌‌‌​​‌‌​‌‌​‌‌​‌​‌​​​‌‌‌​​‌‌​‌​​​​‌‌​​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.ggK7VpuTydpbEV2DnsmG41
 */
import { RawListRemoteZimFilesResponse, RawRemoteZimFileEntry } from '../types/zim.js'

export function isRawListRemoteZimFilesResponse(obj: any): obj is RawListRemoteZimFilesResponse {
  if (!(obj && typeof obj === 'object' && 'feed' in obj)) {
    return false
  }
  if (!obj.feed || typeof obj.feed !== 'object') {
    return false
  }
  if (!('entry' in obj.feed)) {
    return true // entry is optional and may be missing if there are no results
  }

  if ('entry' in obj.feed && typeof obj.feed.entry !== 'object') {
    return false // If entry exists, it must be an object or array
  }

  return true
}

export function isRawRemoteZimFileEntry(obj: any): obj is RawRemoteZimFileEntry {
  return obj && typeof obj === 'object' && 'id' in obj && 'title' in obj && 'summary' in obj
}
