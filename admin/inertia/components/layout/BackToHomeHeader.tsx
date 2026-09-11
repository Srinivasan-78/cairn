/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌‌​​​‌‌‌‌​​​​‌​‌​‌‌‌​​‌‌‌​​‌​‌​​​​‌​​‌​​‌​‌​​‌​​​​‌​​‌‌‌​‌‌​​‌‌​‌‌‌​​‌‌​​​‌​​​‌‌‌​​​​‌‌‌‌​‌​​‌​‌​​‌‌​‌‌‌‌​‌​​‌​‌​​​​​‌‌​‌‌‌​​‌​​‌‌‌‌​‌​‌‌​​‌​‌​​‌​‌‌​‌‌​‌‌‌‌​‌‌​‌‌‌​​‌‌‌​​‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.lxW9BJBvnb8zSzPnOYKons
 */
import { Link } from '@inertiajs/react'
import { IconArrowLeft } from '@tabler/icons-react'
import classNames from '~/lib/classNames'

interface BackToHomeHeaderProps {
  className?: string
  children?: React.ReactNode
}

export default function BackToHomeHeader({ className, children }: BackToHomeHeaderProps) {
  return (
    <div className={classNames('flex border-b border-border-subtle p-4', className)}>
      <div className="justify-self-start">
        <Link href="/home" className="flex items-center">
          <IconArrowLeft className="mr-2" size={24} />
          <p className="text-lg text-text-secondary">Back to Home</p>
        </Link>
      </div>
      <div className="flex-grow flex flex-col justify-center">{children}</div>
    </div>
  )
}
