/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​​​​‌‌​​‌‌​​‌​‌​​‌‌​‌‌‌​‌​‌​​‌‌​‌‌​​‌‌​​‌​‌​‌‌​‌‌​‌​‌‌​​​‌‌​​‌‌​​​‌​‌‌​​​‌​​‌​​‌​​‌​‌‌‌​​‌‌​‌‌​​‌‌​​‌​​​‌‌​​‌​‌‌‌‌‌​‌‌‌​​​​​​‌‌​‌​​​‌​​‌​​‌​‌‌​​‌‌​​‌‌‌​‌‌​​‌‌​​‌‌‌​‌‌​​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.0fSu6emc1bIsfF_p4Ifvgd
 */
import { useEffect, useState } from 'react'
import StyledModal from './StyledModal'
import api from '~/lib/api'

interface ServiceLogsModalProps {
  serviceName: string
  friendlyName: string
  open: boolean
  onClose: () => void
}

/** Shows the tail of a service container's logs with a manual refresh. */
export default function ServiceLogsModal({
  serviceName,
  friendlyName,
  open,
  onClose,
}: ServiceLogsModalProps) {
  const [logs, setLogs] = useState('')
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    const res = await api.getServiceLogs(serviceName, 500)
    setLogs(res?.success ? res.logs || '' : 'Unable to load logs for this container.')
    setLoading(false)
  }

  useEffect(() => {
    if (open) load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, serviceName])

  return (
    <StyledModal
      title={`Logs — ${friendlyName}`}
      open={open}
      onCancel={onClose}
      cancelText="Close"
      onConfirm={load}
      confirmText="Refresh"
      confirmIcon="IconRefresh"
      confirmVariant="outline"
      confirmLoading={loading}
      large
    >
      <pre className="text-xs font-mono whitespace-pre-wrap break-all max-h-[60vh] overflow-auto bg-surface-secondary rounded-md p-3 text-text-primary text-left">
        {logs || (loading ? 'Loading…' : 'No log output.')}
      </pre>
    </StyledModal>
  )
}
