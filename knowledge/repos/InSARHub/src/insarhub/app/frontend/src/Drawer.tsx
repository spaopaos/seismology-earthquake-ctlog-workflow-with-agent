import type { ReactNode, MouseEvent } from 'react'
import type { Theme } from './theme'
import { ResizeHandle } from './useResizable'

interface DrawerShellProps {
  theme: Theme
  rightOffset: number
  width: number
  zIndex: number
  onHandleMouseDown: (e: MouseEvent) => void
  hidden?: boolean
  boxShadow?: string
  children: ReactNode
}

// Shared right-side sliding panel shell — outer fixed box + resize handle,
// used by every L2/L3/L4 job-queue drawer.
export function DrawerShell({ theme: t, rightOffset, width, zIndex, onHandleMouseDown, hidden, boxShadow = '-4px 0 20px rgba(0,0,0,0.25)', children }: DrawerShellProps) {
  return (
    <div style={{
      position: 'fixed', top: 48, right: rightOffset, bottom: 0, width,
      background: t.bg, borderLeft: `1px solid ${t.border}`,
      display: 'flex', flexDirection: 'column', zIndex,
      boxShadow,
      ...(hidden === undefined ? {} : { visibility: hidden ? 'hidden' : 'visible', pointerEvents: hidden ? 'none' : 'auto' }),
    }}>
      <ResizeHandle onMouseDown={onHandleMouseDown} />
      {children}
    </div>
  )
}

interface DrawerHeaderProps {
  theme: Theme
  onClose: () => void
  padding?: string
  gap?: number
  children: ReactNode
}

// Shared drawer header row: title content (children) + close button.
export function DrawerHeader({ theme: t, onClose, padding = '10px 14px', gap, children }: DrawerHeaderProps) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding, borderBottom: `1px solid ${t.border}`,
      background: t.bg2, flexShrink: 0,
      ...(gap === undefined ? {} : { gap }),
    }}>
      {children}
      <button onClick={onClose} style={{ background: 'none', border: 'none',
        cursor: 'pointer', color: t.textMuted, fontSize: 20, lineHeight: 1, padding: '0 4px', flexShrink: 0 }}>×</button>
    </div>
  )
}
