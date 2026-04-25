/**
 * 跨窗口同步（对照 airi `stores/chat-sync.ts` 的 BroadcastChannel 模式）；
 * 聊天窗为数据源，主窗 Live2D 订阅情绪与连接状态。
 */
export const DESKTOP_BUS = 'sunchat:desktop-bus'

export type DesktopBusMessage =
  | { type: 'emotion'; mood_pct: number; label?: string | null }
  | { type: 'connection'; connected: boolean }

export function postDesktopBus(msg: DesktopBusMessage): void {
  try {
    const ch = new BroadcastChannel(DESKTOP_BUS)
    ch.postMessage(msg)
    ch.close()
  } catch {
    /* ignore */
  }
}

export function subscribeDesktopBus(handler: (msg: DesktopBusMessage) => void): () => void {
  let ch: BroadcastChannel
  try {
    ch = new BroadcastChannel(DESKTOP_BUS)
  } catch {
    return () => {}
  }
  ch.onmessage = (ev: MessageEvent<DesktopBusMessage>) => {
    if (ev?.data) handler(ev.data)
  }
  return () => {
    ch.close()
  }
}
