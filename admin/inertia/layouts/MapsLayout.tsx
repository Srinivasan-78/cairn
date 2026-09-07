/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​​​​​‌‌​‌​​​​‌‌​‌‌‌‌​​‌‌​‌​‌​‌‌​​​‌‌​‌​​‌​‌​​​‌​‌‌​‌​‌​​​‌‌‌​‌‌‌​‌‌​​‌‌​‌​​‌​‌‌‌​‌‌‌​‌​​‌‌‌​​‌​‌‌​​‌​‌‌​​‌​​​‌‌‌​‌‌‌​‌​​‌​​‌​‌‌​​‌​‌​‌​‌​‌‌​​‌​​‌‌‌‌​​‌‌​​​​​‌‌‌​​‌​​​‌‌​‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.0ho5cJ-GviwNYdwIeVO0r7
 */
import Footer from '~/components/Footer'

export default function MapsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 w-full bg-desert">{children}</div>
      <Footer />
    </div>
  )
}
