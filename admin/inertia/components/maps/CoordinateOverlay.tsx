/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌​​​‌​‌‌​‌​​​​​‌‌​‌​‌​​‌‌​​‌‌​‌​‌‌​​‌​‌‌‌​‌​​​​‌‌​​​‌​‌‌​‌​‌​​‌‌‌​‌​‌​‌‌​‌‌​‌​‌‌​‌‌​​​​‌‌​​​​​‌​‌​​‌​​‌‌​​‌​​​‌​‌​‌​​​​‌‌​‌​​​​‌‌​‌‌‌​‌‌​​​‌‌​‌‌‌‌​‌​​​‌‌​‌​​​​‌‌​​​​​​‌‌​‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.Qh53Yt1juml0RdT47cz406
 */
type CoordinateOverlayProps = {
  latitude: number
  longitude: number
  x: number
  y: number
}

export default function CoordinateOverlay({
  latitude,
  longitude,
  x,
  y,
}: CoordinateOverlayProps) {
  return (
    <div
      className="pointer-events-none absolute z-[9999] -translate-x-1/2 whitespace-nowrap rounded bg-black/75 px-2 py-1 font-mono text-[11px] text-white"
      style={{
        left: x,
        top: y - 36,
      }}
    >
      {latitude.toFixed(6)}, {longitude.toFixed(6)}
    </div>
  )
}
