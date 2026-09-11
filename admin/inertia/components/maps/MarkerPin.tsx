/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​​‌‌‌​‌​‌‌‌‌‌​‌​​​‌​‌​‌‌‌​​‌​​‌​​​​‌​​​‌‌​‌​‌​​‌‌‌​​‌​‌​​​‌‌‌​‌​‌​​‌‌​‌‌​​​‌​​‌‌​​‌‌​​‌​​‌‌​‌​‌​​​‌​‌​‌​​​‌‌​​‌​‌​‌‌​​‌‌​​​‌​​‌‌‌‌​​​​‌​‌‌​​‌​‌‌​​‌‌​​‌‌‌​‌​‌​​‌‌‌​​​​‌‌‌​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.G_ErB59GSbfMEFVbxYfu8t
 */
import { IconMapPinFilled } from '@tabler/icons-react'

interface MarkerPinProps {
  color?: string
  active?: boolean
}

export default function MarkerPin({ color = '#a84a12', active = false }: MarkerPinProps) {
  return (
    <div className="cursor-pointer" style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.4))' }}>
      <IconMapPinFilled
        size={active ? 36 : 32}
        style={{ color }}
      />
    </div>
  )
}
