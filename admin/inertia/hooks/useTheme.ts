/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​​‌​‌‌​‌​‌​‌​​​​​‌​​‌​‌‌​‌​‌‌​‌​​‌​​‌​​​​‌‌​‌‌‌​​‌‌​​‌​​​‌​​​​​‌​‌​‌​‌‌‌​‌‌‌​‌​‌​​‌‌‌​​​​​‌‌‌​​‌​​‌‌​​​​​‌​​​​​‌​‌​‌​‌‌​​‌‌‌​‌​​​‌​​‌​​​​​‌​‌‌​‌​‌‌‌‌​‌​​‌​​‌​​‌​‌​​​‌‌‌​‌‌​‌​​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.-PKZHndAWu890AVtH-zIGh
 */
import { useState, useEffect, useCallback } from 'react'
import api from '~/lib/api'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'cairn:theme'

function getInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'dark' || stored === 'light') return stored
  } catch {}
  return 'light'
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme)

  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
    try {
      localStorage.setItem(STORAGE_KEY, newTheme)
    } catch {}
    // Fire-and-forget KV store sync for cross-device persistence
    api.updateSetting('ui.theme', newTheme).catch(() => {})
  }, [])

  const toggleTheme = useCallback(() => {
    setThemeState((prev) => {
      const next = prev === 'light' ? 'dark' : 'light'
      document.documentElement.setAttribute('data-theme', next)
      try {
        localStorage.setItem(STORAGE_KEY, next)
      } catch {}
      api.updateSetting('ui.theme', next).catch(() => {})
      return next
    })
  }, [])

  // Apply theme on mount
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [])

  return { theme, setTheme, toggleTheme }
}
