import { useAuthStore } from '../stores/auth'

type AwarenessHandler = (users: any[]) => void
type RemoteChangeHandler = (content: string) => void

class CollabWebSocket {
  private ws: WebSocket | null = null
  private currentNoteId: number = 0
  private awarenessHandlers: AwarenessHandler[] = []
  private remoteChangeHandlers: RemoteChangeHandler[] = []
  private reconnectTimer: any = null
  private cursorInterval: any = null
  private cursor: { line: number; col: number } | null = null
  private currentContent: string = ''

  connect(noteId: number): void {
    if (this.currentNoteId === noteId && this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.teardownWS()
    this.currentNoteId = noteId

    const authStore = useAuthStore()
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const token = authStore.token
    const wsUrl = `${protocol}//${host}/ws/notes/${noteId}?token=${token}`

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      this.ws?.send(JSON.stringify({ type: 'sync-request' }))
      this.startCursorSync()
    }

    this.ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'sync-response' && data.content !== undefined) {
            this.currentContent = data.content
            this.remoteChangeHandlers.forEach(h => h(data.content))
          } else if (data.type === 'sync' && data.content !== undefined) {
            this.currentContent = data.content
            this.remoteChangeHandlers.forEach(h => h(data.content))
          } else if (data.type === 'awareness') {
            this.awarenessHandlers.forEach(h => h(data.users))
          }
        } catch { /* ignore */ }
      }
    }

    this.ws.onclose = () => {
      this.stopCursorSync()
      this.reconnectTimer = setTimeout(() => {
        if (this.currentNoteId) this.connect(this.currentNoteId)
      }, 3000)
    }

    this.ws.onerror = () => { this.ws?.close() }
  }

  syncLocalChange(content: string) {
    this.currentContent = content
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'sync', content }))
    }
  }

  onRemoteChange(callback: (content: string) => void) {
    this.remoteChangeHandlers.push(callback)
  }

  setCursor(line: number, col: number) {
    this.cursor = { line, col }
  }

  private startCursorSync() {
    this.cursorInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN && this.cursor) {
        this.ws.send(JSON.stringify({ type: 'cursor', cursor: this.cursor }))
      }
    }, 200)
  }

  private stopCursorSync() {
    if (this.cursorInterval) { clearInterval(this.cursorInterval); this.cursorInterval = null }
  }

  saveContent() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'save', content: this.currentContent }))
    }
  }

  onAwareness(handler: AwarenessHandler) {
    this.awarenessHandlers.push(handler)
  }

  get isConnected() { return this.ws?.readyState === WebSocket.OPEN }

  /** 仅关闭 WebSocket，保留 handlers（重连后继续使用） */
  private teardownWS() {
    clearTimeout(this.reconnectTimer)
    this.reconnectTimer = null
    this.stopCursorSync()
    this.currentNoteId = 0
    this.currentContent = ''
    if (this.ws) { this.ws.onclose = null; this.ws.close(); this.ws = null }
  }

  /** 完全断开，清空所有 handlers */
  disconnect() {
    this.teardownWS()
    this.awarenessHandlers = []
    this.remoteChangeHandlers = []
  }
}

export const collabWS = new CollabWebSocket()
