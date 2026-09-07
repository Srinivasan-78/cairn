/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​​​‌​​‌‌​‌​‌‌​‌​‌‌​​‌​‌​​‌‌​​​‌‌‌​‌‌​​‌​​​​‌​​‌​‌‌​​​​‌​​​​‌‌​‌‌​​‌​‌​‌‌​‌‌​​​‌​​​​‌‌​​‌‌​‌​‌​​‌‌​​​​​‌‌​‌‌‌‌​‌‌​​​​‌​‌‌‌‌​‌​​‌‌‌​​​‌​‌​​‌​​​​‌‌‌‌​​​​‌‌​​​‌​​‌​‌​‌‌​​‌‌‌​​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.BkYLvBXCelC50oazqHxbVp
 */
import { useQuery } from '@tanstack/react-query'
import api from '~/lib/api'
import { ContentAutoUpdateStatus } from '../../types/system'

export const useContentAutoUpdateStatus = () => {
  return useQuery<ContentAutoUpdateStatus | undefined>({
    queryKey: ['content-auto-update-status'],
    queryFn: () => api.getContentAutoUpdateStatus(),
    refetchOnWindowFocus: false,
  })
}
