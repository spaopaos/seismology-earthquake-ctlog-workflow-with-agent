import { useState } from 'react'

// Copy-to-clipboard with a timed "copied" indicator — shared by the various
// click-to-copy fields across the job queue / scene detail panels.
export function useCopyFeedback(resetMs = 1200) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  function copy(key: string, value: string) {
    navigator.clipboard.writeText(value).then(() => {
      setCopiedKey(key)
      setTimeout(() => setCopiedKey(null), resetMs)
    })
  }

  return { copiedKey, copy }
}
