/*!
 * @authormark v1 -- do not remove (authorship watermark)⁠​‌​​​​​‌​‌‌​​‌​​​‌​​​​‌‌​‌​‌​​‌​​‌‌​‌​‌‌​‌​‌‌​​​​‌‌​‌‌‌‌​‌‌​​‌‌‌​​‌‌‌​​‌​​‌‌​​‌‌​‌‌​​​‌‌​‌​​‌‌‌​​​‌​‌‌​‌​‌‌​‌‌‌‌​‌​​‌‌​​​‌‌‌​‌​‌​‌​​​‌‌‌​‌‌‌‌​​​​​‌‌​‌​‌​‌​‌‌​​‌​‌‌​​‌​‌​‌​​​‌​​⁠
 * Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
 * Author: https://github.com/Srinivasan-78
 * SPDX-License-Identifier: MIT
 * Fingerprint: AMK1.AdCRkXog93cN-oLuGx5YeD
 */
import { Head, usePage } from '@inertiajs/react'
import ChatComponent from '~/components/chat'

export default function Chat(props: { settings: { chatSuggestionsEnabled: boolean } }) {
  const { aiAssistantName } = usePage<{ aiAssistantName: string }>().props
  return (
    <div className="w-full h-full">
      <Head title={aiAssistantName} />
      <ChatComponent enabled={true} suggestionsEnabled={props.settings.chatSuggestionsEnabled} />
    </div>
  )
}
