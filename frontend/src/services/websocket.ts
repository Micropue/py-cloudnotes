import * as Y from 'yjs'
import { useAuthStore } from '../stores/auth'

type AwarenessHandler = (users: any[]) => void

class CollabWebSocket {
  private ws: WebSocket | null = null
  private ydoc: Y.Doc | null = null
  private ytext: Y.Text | null = null
  private currentNoteId: number = 0
  private awarenessHandlers: AwarenessHandler[] = []
  private reconnectTimer: any = null
  private cursorInterval: any = null

  private cursor: { line: number; col: number } | null = null
  private _isLocalChange = false

  connect(noteId: number): { ydoc: Y.Doc; ytext: Y.Text } {
    // 如果已经连接同一篇文档，复用
    if (this.currentNoteId === noteId && this.ydoc && this.ytext && this.ws?.readyState === WebSocket.OPEN) {
      return { ydoc: this.ydoc, ytext: this.ytext }
    }

    this.disconnect()
    this.currentNoteId = noteId

    this.ydoc = new Y.Doc()
    this.ytext = this.ydoc.getText('content')

    // 本地变更 → 发送到服务器
    this.ydoc.on('update', (update: Uint8Array) => {
      if (this._isLocalChange && this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(update)
      }
    })

    const authStore = useAuthStore()
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const token = authStore.token
    const wsUrl = `${protocol}//${host}/ws/notes/${noteId}?token=${token}`

    this.ws = new WebSocket(wsUrl)
    this.ws.binaryType = 'arraybuffer'

    this.ws.onopen = () => {
      this.ws?.send(JSON.stringify({ type: 'sync-request' }))
      this.startCursorSync()
    }

    this.ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // 远程 Yjs 更新
        const update = new Uint8Array(event.data)
        this._isLocalChange = false
        Y.applyUpdate(this.ydoc!, update)
        this._isLocalChange = true
      } else if (typeof event.data === 'string') {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'sync-response' && data.content && this.ytext) {
            if (this.ytext.toString() === '') {
              this.ydoc!.transact(() => {
                this.ytext!.delete(0, this.ytext!.length)
                this.ytext!.insert(0, data.content)
              })
            }
          } else if (data.type === 'awareness') {
            this.awarenessHandlers.forEach((h) => h(data.users))
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

    this._isLocalChange = true
    return { ydoc: this.ydoc, ytext: this.ytext }
  }

  /** 本地编辑同步到 Yjs（由 textarea input 事件调用） */
  syncLocalChange(content: string) {
    if (!this.ytext || !this.ydoc || !this._isLocalChange) return
    this.ydoc.transact(() => {
      this.ytext!.delete(0, this.ytext!.length)
      this.ytext!.insert(0, content)
    })
  }

  /** 监听 Yjs 远程变更 */
  onRemoteChange(callback: (content: string) => void) {
    this.ytext?.observe(() => {
      if (this._isLocalChange) return // 跳过本地回显
      callback(this.ytext!.toString())
    })
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
    if (this.ws?.readyState === WebSocket.OPEN && this.ytext) {
      this.ws.send(JSON.stringify({ type: 'save', content: this.ytext.toString() }))
    }
  }

  onAwareness(handler: AwarenessHandler) {
    this.awarenessHandlers.push(handler)
  }

  get isConnected() { return this.ws?.readyState === WebSocket.OPEN }

  disconnect() {
    clearTimeout(this.reconnectTimer)
    this.reconnectTimer = null
    this.stopCursorSync()
    this.awarenessHandlers = []
    this._isLocalChange = false
    this.currentNoteId = 0
    if (this.ws) { this.ws.onclose = null; this.ws.close(); this.ws = null }
    if (this.ydoc) { this.ydoc.destroy(); this.ydoc = null; this.ytext = null }
  }
}

export const collabWS = new CollabWebSocket()
