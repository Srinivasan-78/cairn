/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌‌​‌​‌‌‌​​​​​‌‌​​‌​​​‌‌​​‌‌​​‌​​​​​‌​​‌‌​‌​​​​‌‌​‌‌​​‌‌‌‌​‌​​‌​​‌‌‌‌​​‌‌​‌‌​​​‌​‌‌​‌​‌​​‌‌‌‌​‌‌‌​​​​​​‌‌​​‌‌​‌‌​‌‌‌​​‌​​‌​‌​​‌‌​‌‌‌‌​​‌‌‌​​​​‌‌​‌‌​​​‌​‌‌​‌​​‌‌​​‌‌‌​​‌‌‌​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.mpdfA46zO6-Op3nJo8lZg8
 */
import { useQuery } from '@tanstack/react-query'
import { FileEntry } from '../../types/files'
import api from '~/lib/api'

const useMapRegionFiles = () => {
  return useQuery<FileEntry[]>({
    queryKey: ['map-region-files'],
    queryFn: () => api.listMapRegionFiles(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export default useMapRegionFiles
