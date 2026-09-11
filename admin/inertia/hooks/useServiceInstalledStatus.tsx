/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​​​‌‌​‌​​‌‌​‌​‌‌‌‌​​‌​​‌‌​‌​‌​​‌‌‌​​​​‌‌​‌​​‌​‌‌​‌‌​‌​‌​​‌‌‌‌​‌​‌​‌​​​‌​​​‌‌‌​‌​​‌​‌‌​‌​‌‌​‌​​‌​​​‌‌​​​‌​‌‌​‌​‌‌​‌‌​‌​‌​‌‌​​‌​​‌‌​​‌​​‌​‌‌​‌​​​‌‌​​​​​​‌‌​​‌‌​​‌‌​‌‌‌​‌​​‌‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.CMy58imOTGKZF-mY2Z037N
 */
import { useQuery } from '@tanstack/react-query'
import { ServiceSlim } from '../../types/services'
import api from '~/lib/api'

const useServiceInstalledStatus = (serviceName: string) => {
  const { data, isFetching } = useQuery<ServiceSlim[] | undefined>({
    queryKey: ['installed-services'],
    queryFn: () => api.getSystemServices(),
  })

  const isInstalled = data?.some(
    (service) => service.service_name === serviceName && service.installed
  )

  return { isInstalled, loading: isFetching }
}

export default useServiceInstalledStatus
