/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​‌​​‌​​‌​‌​‌​​​‌​‌​‌​‌​‌​​‌​‌​​‌​​‌​‌​​‌‌​‌​‌​​‌​‌​​​​​​‌‌​‌‌‌​‌​​‌‌‌​​‌​​‌​​‌​‌​​‌​​‌​​‌‌​​​‌​‌​​‌‌​‌​‌​​​‌​​​‌‌​‌‌​‌​‌​​​‌​​​‌‌​‌‌‌‌​‌‌​​‌​​​‌‌​‌​‌​​‌​‌​​‌‌​‌‌​‌‌​‌​‌‌​‌‌‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.RTUJJjP7NII1MDmDodjSmo
 */
import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import StyledSidebar from '~/components/StyledSidebar'
import api from '~/lib/api'

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const { data, isLoading } = useQuery<Array<{ title: string; slug: string }>>({
    queryKey: ['docs'],
    queryFn: () => api.listDocs(),
    refetchOnWindowFocus: false,
    staleTime: Infinity,
  })

  const items = useMemo(() => {
    if (isLoading || !data) return []

    return data.map((doc) => ({
      name: doc.title,
      href: `/docs/${doc.slug}`,
      current: false,
    }))
  }, [data, isLoading])

  return (
    <div className="min-h-screen flex flex-row bg-desert-white">
      <StyledSidebar title="Documentation" items={items} />
      {children}
    </div>
  )
}
