/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌‌​‌‌‌​‌​​​​​‌​‌‌​​​‌‌​‌​​‌​‌​​‌​​‌​​‌​‌​‌‌​​​​‌​‌​​‌​​​‌‌​‌​​​​‌​‌‌​‌​‌‌​‌​‌​​‌​‌‌​​​​‌‌​​​‌‌​‌‌​‌‌​‌​‌‌‌‌​‌​​‌​​‌​‌​​​‌‌​‌​​​‌​‌​​‌‌​‌‌​‌​​​​‌​​‌​​​​‌‌‌‌​‌​​​‌‌​‌‌​​‌‌​‌‌‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.7AcJIXR4-jXcmzJ4ShHz6n
 */
import { IconMessages } from '@tabler/icons-react'

interface ChatButtonProps {
  onClick: () => void
}

export default function ChatButton({ onClick }: ChatButtonProps) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 z-40 p-4 bg-desert-green text-white rounded-full shadow-lg hover:bg-desert-green/90 transition-all duration-200 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-desert-green focus:ring-offset-2 cursor-pointer"
      aria-label="Open chat"
    >
      <IconMessages className="h-6 w-6" />
    </button>
  )
}
