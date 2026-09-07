/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌‌‌​​‌‌‌​‌‌​​‌​‌‌‌‌‌​​‌‌​​​​​‌​​‌​‌​​‌​‌‌​​​​‌​​‌​‌‌​‌‌​‌​‌​​​‌‌‌​​​​‌​‌‌‌‌‌​‌​​‌​‌​​‌‌‌​​‌‌​‌​​​‌‌​​‌​‌‌‌‌‌​‌​​​​​‌​‌​​​‌‌‌​‌‌‌​‌‌‌​‌​‌​​​‌​‌​‌​‌‌‌​‌​​​‌​​​‌‌​‌​​​​​‌‌​​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.nv_0JXKj8_JsF_AGwQWDh0
 */
import { useEffect, useState } from 'react'
import { useTransmit } from 'react-adonis-transmit'
import { InstallActivityFeedProps } from '~/components/InstallActivityFeed'
import { BROADCAST_CHANNELS } from '../../constants/broadcast'

export default function useServiceInstallationActivity() {
  const { subscribe } = useTransmit()
  const [installActivity, setInstallActivity] = useState<InstallActivityFeedProps['activity']>([])

  useEffect(() => {
    const unsubscribe = subscribe(BROADCAST_CHANNELS.SERVICE_INSTALLATION, (data: any) => {
      setInstallActivity((prev) => [
        ...prev,
        {
          service_name: data.service_name ?? 'unknown',
          type: data.status ?? 'unknown',
          timestamp: new Date().toISOString(),
          message: data.message ?? 'No message provided',
        },
      ])
    })

    return () => {
      unsubscribe()
    }
  }, [])

  return installActivity
}
