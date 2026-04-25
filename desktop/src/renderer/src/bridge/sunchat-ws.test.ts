import { describe, expect, it } from 'vitest'

import { WS_PROTOCOL_NAME, WS_PROTOCOL_VERSION } from './sunchat-ws'

describe('sunchat-ws', () => {
  it('protocol id matches src/sunchat/api/ws_protocol.py', () => {
    expect(WS_PROTOCOL_NAME).toBe('sunchat-ws')
    expect(WS_PROTOCOL_VERSION).toBe('1')
  })

  it('client chat payload shape matches ws_session (type: chat, content string)', () => {
    const payload = JSON.stringify({ type: 'chat', content: '你好' })
    expect(JSON.parse(payload)).toEqual({
      type: 'chat',
      content: '你好',
    })
  })
})
