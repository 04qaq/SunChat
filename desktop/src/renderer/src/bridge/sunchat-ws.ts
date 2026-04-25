/**
 * SunChat WebSocket 客户端：与 `sunchat.application.ws_session` 及 `ws_protocol` 对齐。
 * 不依赖 airi `server-sdk`。
 */

export const WS_PROTOCOL_NAME = 'sunchat-ws'
export const WS_PROTOCOL_VERSION = '1'

export type ServerMessage =
  | { type: 'session'; session_id: string; protocol: { name: string; version: string }; psychology: Record<string, unknown> }
  | { type: 'emotion'; mood_pct: number; session_id: string; label?: string }
  | { type: 'token'; delta: string }
  | { type: 'done' }
  | { type: 'error'; message: string }

export interface SunchatWsHandlers {
  onOpen?: () => void
  onClose?: (ev: CloseEvent) => void
  onMessage?: (msg: ServerMessage) => void
  onError?: (ev: Event) => void
}

export interface SunchatWsClient {
  readonly url: string
  connect: () => void
  disconnect: () => void
  sendChat: (content: string) => void
  readonly readyState: number
}

export function createSunchatWs(
  url: string,
  handlers: SunchatWsHandlers = {},
): SunchatWsClient {
  let ws: WebSocket | null = null

  return {
    url,
    get readyState() {
      return ws?.readyState ?? WebSocket.CLOSED
    },
    connect() {
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        ws.close()
      }
      ws = new WebSocket(url)
      ws.addEventListener('open', () => handlers.onOpen?.())
      ws.addEventListener('close', (ev) => handlers.onClose?.(ev))
      ws.addEventListener('error', (ev) => handlers.onError?.(ev))
      ws.addEventListener('message', (ev) => {
        try {
          const raw = JSON.parse(String(ev.data)) as ServerMessage
          handlers.onMessage?.(raw)
        } catch {
          handlers.onMessage?.({ type: 'error', message: 'Invalid JSON from server' })
        }
      })
    },
    disconnect() {
      ws?.close()
      ws = null
    },
    sendChat(content: string) {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        throw new Error('WebSocket is not open')
      }
      ws.send(JSON.stringify({ type: 'chat', content }))
    },
  }
}
