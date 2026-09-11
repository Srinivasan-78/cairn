/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​‌‌​​‌‌‌​‌​​​‌‌​‌‌‌‌​‌​‌‌​​‌​‌​​​‌‌​​‌‌‌‌​‌​​‌‌‌​​​​​‌‌​​‌‌​​‌‌‌​‌‌​​‌​​​​​‌​‌​‌‌​‌​​‌‌​‌​‌‌​​‌‌​‌‌‌​‌‌‌​​​‌​‌​​‌​​‌​‌​​‌​​​​‌​‌​‌‌​​​‌‌​​​‌​‌​‌​‌​‌​‌​‌​‌​​​‌​​​​​‌​‌‌​​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.ftoYFzpfvAZk7qIHV1UTAd
 */
import clsx from 'clsx'

interface BouncingDotsProps {
  text: string
  containerClassName?: string
  textClassName?: string
}

export default function BouncingDots({ text, containerClassName, textClassName }: BouncingDotsProps) {
  return (
    <div className={clsx("flex items-center justify-center gap-2", containerClassName)}>
      <span className={clsx("text-text-secondary", textClassName)}>{text}</span>
      <span className="flex gap-1 mt-1">
        <span
          className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce"
          style={{ animationDelay: '0ms' }}
        />
        <span
          className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce"
          style={{ animationDelay: '150ms' }}
        />
        <span
          className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce"
          style={{ animationDelay: '300ms' }}
        />
      </span>
    </div>
  )
}
