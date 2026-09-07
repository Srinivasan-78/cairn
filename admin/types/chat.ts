/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌​​‌​‌‌‌​​‌‌​‌​‌​​‌‌​‌‌​​‌‌​​​‌‌​​​‌​‌‌‌​​​‌​‌‌‌​‌‌‌​‌​‌‌​​‌​‌‌​‌‌​​​​‌‌​‌‌‌​‌‌​​‌​​​‌​‌​‌‌​​‌‌​​​​‌​‌​​​‌‌‌​​‌‌​​​‌​‌‌‌‌​​​​‌‌‌​​​‌​‌​​‌​​​​‌​‌​​‌‌​‌​‌​​​​​‌‌​​‌‌‌​‌‌‌​​‌‌⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.IsSf1qwYl7dVaG1xqHSPgs
 */
export interface ChatMessage {
  id: string
  role: 'system' | 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
  thinking?: string
  isThinking?: boolean
  thinkingDuration?: number
}

export interface ChatSession {
  id: string
  title: string
  lastMessage?: string
  timestamp: Date
}
