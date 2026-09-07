/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌‌‌​​‌‌‌‌​​‌​‌​​‌​‌​​​‌‌‌​​‌​‌​‌​‌‌​​​‌‌​​​‌​‌‌‌​‌​‌​​‌‌​​​​​‌​​​​‌‌​‌​‌​​‌​​‌​‌‌‌‌‌​‌‌​‌​‌​​‌‌​‌‌‌​​‌​​‌‌‌‌​‌​‌​​​​​‌‌​​​‌‌​‌‌​​​‌​​‌​​‌​‌​​‌‌​‌​​​​‌‌‌​​‌​​‌‌​‌​​‌​‌‌‌‌​​‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.nyJ9V1u0CR_jnOPcbJhriy
 */
import { createContext, useContext } from 'react'
import { useTheme, Theme } from '~/hooks/useTheme'

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType>({
  theme: 'light',
  setTheme: () => {},
  toggleTheme: () => {},
})

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const themeState = useTheme()
  return (
    <ThemeContext.Provider value={themeState}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useThemeContext() {
  return useContext(ThemeContext)
}
