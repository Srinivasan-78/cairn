/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​​​​‌​‌​​​‌​‌‌​‌​‌‌​‌‌‌​​​‌​‌‌​‌‌‌‌​‌​‌‌‌‌‌​‌​​​‌‌​​‌​​​​​‌​‌‌​‌‌‌​​​‌‌​‌​‌​​‌‌​​​​​‌‌​​​‌​​‌‌‌‌​​​​‌‌​‌​‌​​‌‌​‌​‌​​‌‌‌​​‌‌​‌​‌​‌​​​‌​​‌‌​‌​‌​​‌‌‌​​‌​‌​‌‌​​‌‌​​​​‌​‌​‌‌​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.0Qkqo_FAn50bxjjsTMNVaX
 */
import { useQuery } from '@tanstack/react-query'
import api from '~/lib/api'
import { AppAutoUpdateStatus } from '../../types/system'

export const useAppAutoUpdateStatus = () => {
  return useQuery<AppAutoUpdateStatus | undefined>({
    queryKey: ['app-auto-update-status'],
    queryFn: () => api.getAppAutoUpdateStatus(),
    refetchOnWindowFocus: false,
  })
}
