/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​‌​‌​‌‌​‌‌​‌​‌​​​‌​​​‌​​‌‌​‌​‌‌‌​‌‌‌​‌‌‌​‌‌​​​‌‌​​‌​​‌​‌​​​‌​‌​‌​​‌‌​‌​​‌‌‌‌​‌​​​‌​‌​​‌‌​​‌​​‌​​‌​‌‌​‌​​‌‌‌​​‌‌‌​‌​‌​‌​‌​‌​‌​‌​​‌‌‌​​‌‌‌​​​‌​‌​‌​‌​​​‌‌‌​​​‌​‌‌‌​‌‌​​‌​‌‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.emDMwv2QSOE2KNuUNqTqvY
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import { SystemInformationResponse } from '../../types/system'
import api from '~/lib/api'

export type UseSystemInfoProps = Omit<
  UseQueryOptions<SystemInformationResponse | undefined>,
  'queryKey' | 'queryFn'
> & {}

export const useSystemInfo = (props: UseSystemInfoProps) => {
  const queryData = useQuery<SystemInformationResponse | undefined>({
    ...props,
    queryKey: ['system-info'],
    queryFn: async () => await api.getSystemInfo(),
    refetchInterval: 45000, // Refetch every 45 seconds
  })

  return queryData
}
