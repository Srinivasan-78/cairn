/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​​‌​‌​​‌‌​‌‌‌​‌​​​​‌‌​‌​​​​‌‌​‌​​​‌​​​‌‌​​‌​​​‌‌​‌​​​​​‌‌​​‌‌​‌‌​​​‌​​‌‌​​‌‌​​‌​​​‌‌‌​‌​​​‌​‌​‌‌‌​‌‌‌​​‌‌‌​​​​‌​‌​‌‌​​‌​​‌‌​‌​‌‌‌​​‌‌​‌​‌‌‌‌‌​‌‌‌‌​​​​‌​‌​‌‌​​‌‌‌​‌​​​‌​‌‌​‌​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.E7CCDdh3bfGEw8VMs_xVtZ
 */
import { useState, Fragment } from 'react'
import { ModalContext } from '~/context/ModalContext'

export interface ModalsProviderProps {
  children: React.ReactNode
}

const ModalsProvider: React.FC<ModalsProviderProps> = ({ children }) => {
  const [modals, setModals] = useState<Record<string, React.ReactNode>>({})
  const [, setPreventCloseOnOverlayClick] = useState<boolean>(false)

  const openModal = (content: React.ReactNode, id: string, preventClose = false) => {
    setModals((prev) => ({
      ...prev,
      [id]: content,
    }))
    setPreventCloseOnOverlayClick(preventClose)
  }

  const closeModal = (id: string) => {
    setModals((prev) => {
      const newModals = { ...prev }
      delete newModals[id]
      return newModals
    })
    if (Object.keys(modals).length === 1) {
      setPreventCloseOnOverlayClick(false) // reset if last modal is closed
    }
  }

  const closeAllModals = () => {
    setModals({})
    setPreventCloseOnOverlayClick(false) // reset
  }

  const _getCurrentModals = () => {
    return modals
  }

  return (
    <ModalContext.Provider value={{ openModal, closeModal, closeAllModals, _getCurrentModals }}>
      {children}
      {Object.keys(modals).length === 0 ? null : (
        <>
          {Object.entries(modals).map(([key, node]) => (
            <Fragment key={key}>{node}</Fragment>
          ))}
        </>
      )}
    </ModalContext.Provider>
  )
}

export default ModalsProvider
