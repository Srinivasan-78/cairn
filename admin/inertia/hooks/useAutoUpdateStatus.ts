/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​​​‌​‌‌‌‌​​​​‌‌​‌‌​​​‌​‌​‌​​​​‌‌​​​​​‌​​‌​​‌​‌‌​‌‌​​​‌‌​​‌​​​​‌‌​​‌​​‌​‌​​‌‌​‌​​‌‌‌‌​‌‌‌‌​​​​​‌‌​​‌​​‌​​‌​​‌​‌​‌​​‌​​‌​‌​​‌‌​‌​​‌​​​​‌‌​​‌​​​‌​​​​​‌​‌​‌​​​​​​‌‌​‌​‌​‌‌‌‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.qxlT0Ild2SOx2IRSHdAP5y
 */
import { useQuery } from '@tanstack/react-query'
import api from '~/lib/api'
import { AutoUpdateStatus } from '../../types/system'

export const useAutoUpdateStatus = () => {
  return useQuery<AutoUpdateStatus | undefined>({
    queryKey: ['auto-update-status'],
    queryFn: () => api.getAutoUpdateStatus(),
    refetchOnWindowFocus: false,
  })
}
