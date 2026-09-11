/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌​‌‌​‌​​‌‌​​​​‌‌​​‌‌​‌‌​‌​​​​‌‌​​​‌​​​‌‌​‌​‌​‌‌​‌‌‌​​‌​‌​​​‌​‌​​‌​‌​​‌​​‌‌‌​​‌​​​​‌​​‌​​‌‌‌​​​‌‌‌​​​​‌​‌​​​​​‌​​‌​‌‌​‌​​‌​‌​​‌​‌‌​‌​​‌‌​‌​‌‌​​‌‌​‌​​​​‌‌​​​​​‌‌‌​‌‌​​​‌‌​​‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.KL3hb5nQJNBN8PKJZk40v3
 */
import { createContext, useContext, ReactNode } from 'react'

interface ModalContextProps {
  openModal: (content: ReactNode, id: string, preventClose?: boolean) => void
  closeModal: (id: string) => void
  closeAllModals: () => void
  _getCurrentModals: () => Record<string, ReactNode>
  preventCloseOnOverlayClick?: boolean
}

export const ModalContext = createContext<ModalContextProps | undefined>(undefined)

export const useModals = () => {
  const context = useContext(ModalContext)
  if (!context) {
    throw new Error('useModal must be used within a ModalProvider')
  }
  return context
}
