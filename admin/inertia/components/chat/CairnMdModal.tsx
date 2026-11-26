import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { IconX } from '@tabler/icons-react'
import StyledButton from '~/components/StyledButton'
import MarkdownEditor from '~/components/MarkdownEditor'
import { useNotifications } from '~/context/NotificationContext'
import api from '~/lib/api'

interface CairnMdModalProps {
  aiAssistantName?: string
  onClose: () => void
}

// Seeded into the editor when no Cairn.md exists yet. Nothing is written to disk
// until the user saves, so this is purely a starting point they can replace.
const CAIRN_MD_TEMPLATE = `# Cairn.md

<!--
This file holds custom instructions for your AI assistant. Everything here is
sent to the assistant as a system prompt on every chat — use it to set persona,
tone, priorities, and standing rules.

It is also stored on disk at storage/Cairn.md, so you can edit it directly.
Replace this template with your own instructions, then click Save.
-->

## About me

- (e.g. I'm setting up an off-grid homestead in a cold climate.)

## How the assistant should respond

- Be concise and practical.
- Prioritize safety and proven methods.
`

export default function CairnMdModal({ aiAssistantName, onClose }: CairnMdModalProps) {
  const queryClient = useQueryClient()
  const { addNotification } = useNotifications()
  const [content, setContent] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['cairn-md'],
    queryFn: () => api.getCairnMd(),
  })

  // Seed the editor once the file loads: existing content, or the template when empty.
  useEffect(() => {
    if (data && content === null) {
      setContent(data.content.trim().length > 0 ? data.content : CAIRN_MD_TEMPLATE)
    }
  }, [data, content])

  const saveMutation = useMutation({
    mutationFn: (value: string) => api.saveCairnMd(value),
    onSuccess: (result) => {
      if (!result?.success) {
        addNotification({ type: 'error', message: 'Failed to save Cairn.md.' })
        return
      }
      addNotification({ type: 'success', message: 'Cairn.md saved. It applies to new messages.' })
      queryClient.invalidateQueries({ queryKey: ['cairn-md'] })
      onClose()
    },
    onError: (error: any) => {
      addNotification({ type: 'error', message: error?.message || 'Failed to save Cairn.md.' })
    },
  })

  const assistantName = aiAssistantName?.trim() || 'your AI assistant'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/30 backdrop-blur-sm transition-opacity">
      <div className="bg-surface-primary rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b border-border-subtle shrink-0">
          <div>
            <h2 className="text-2xl font-semibold text-text-primary">Cairn.md</h2>
            <p className="text-sm text-text-muted mt-1">
              Custom instructions passed to {assistantName} as a system prompt on every chat.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface-secondary rounded-lg transition-colors"
          >
            <IconX className="h-6 w-6 text-text-muted" />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 p-6">
          {isLoading || content === null ? (
            <div className="py-16 text-center text-text-muted">Loading…</div>
          ) : (
            <div className="rounded-lg border border-border-subtle overflow-hidden h-[55vh]">
              <MarkdownEditor initialValue={content} onChange={setContent} className="h-full text-sm" />
            </div>
          )}
          <p className="text-xs text-text-muted mt-3">
            Tip: this file is also stored on disk at{' '}
            <code className="font-mono">storage/Cairn.md</code> and can be edited directly.
          </p>
        </div>

        <div className="flex items-center justify-end gap-3 p-6 border-t border-border-subtle shrink-0">
          <StyledButton variant="outline" onClick={onClose} disabled={saveMutation.isPending}>
            Cancel
          </StyledButton>
          <StyledButton
            variant="primary"
            icon="IconCircleCheck"
            onClick={() => content !== null && saveMutation.mutate(content)}
            loading={saveMutation.isPending}
            disabled={content === null}
          >
            Save
          </StyledButton>
        </div>
      </div>
    </div>
  )
}
