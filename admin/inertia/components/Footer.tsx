/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​​​‌​​‌‌​‌‌​​​‌​​​‌​‌​‌​‌​​‌‌​‌​‌​‌​​​‌​‌​‌​‌​‌​‌​​‌​​‌‌​‌‌​‌​‌​‌‌​​‌​‌​​‌‌​​​​‌‌‌​​​​‌​​​‌‌​​‌‌​‌‌‌​​‌‌​‌​‌​​‌‌‌​‌​‌​‌​‌‌​‌​​‌​​‌​‌‌​‌​​‌​‌​​​‌​‌‌​‌​‌​‌​​‌‌​‌​​‌​​​​‌​​​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.blESTURmYL8FnjuZKJ-SHD
 */
import { useState } from 'react'
import { usePage } from '@inertiajs/react'
import { UsePageProps } from '../../types/system'
import ThemeToggle from '~/components/ThemeToggle'
import { IconBug } from '@tabler/icons-react'
import DebugInfoModal from './DebugInfoModal'

export default function Footer() {
  const { appVersion } = usePage().props as unknown as UsePageProps
  const [debugModalOpen, setDebugModalOpen] = useState(false)

  return (
    <footer>
      <div className="flex items-center justify-center gap-3 border-t border-border-subtle py-4">
        <p className="text-sm/6 text-text-secondary">
          Cairn&trade; Command Center v{appVersion}
        </p>
        <span className="text-gray-300">|</span>
        <button
          onClick={() => setDebugModalOpen(true)}
          className="text-sm/6 text-gray-500 hover:text-desert-green flex items-center gap-1 cursor-pointer"
        >
          <IconBug className="size-3.5" />
          Debug Info
        </button>
        <ThemeToggle />
      </div>
      <DebugInfoModal open={debugModalOpen} onClose={() => setDebugModalOpen(false)} />
    </footer>
  )
}
