/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌​‌​​​​‌​‌‌​‌​‌‌‌​‌​‌​‌‌​‌‌‌​​‌‌​‌​‌​​‌‌‌​​​​​‌‌​‌‌​‌​‌‌​‌​‌‌​​‌‌‌​​‌​‌​​‌‌‌​​‌​‌‌​​‌​‌‌​‌‌​​​‌​​​​‌​​‌‌‌‌​​​​‌​​​​‌‌​‌‌​​​‌‌​​‌‌​​‌​​‌‌​​‌​​​‌‌‌‌​‌​​‌‌​​​‌‌​‌​​‌‌​‌​​‌‌​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.T-unjpmk9NYlBxCc2dzcM4
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import api from '~/lib/api'
import { KVStoreKey } from '../../types/kv_store';

export type UseSystemSettingProps = Omit<
  UseQueryOptions<{ key: string; value: any } | undefined>,
  'queryKey' | 'queryFn'
> & {
  key: KVStoreKey
}

export const useSystemSetting = (props: UseSystemSettingProps) => {
  const { key, ...queryOptions } = props

  const queryData = useQuery<{ key: string; value: any } | undefined>({
    ...queryOptions,
    queryKey: ['system-setting', key],
    queryFn: async () => await api.getSetting(key),
  })

  return queryData
}
