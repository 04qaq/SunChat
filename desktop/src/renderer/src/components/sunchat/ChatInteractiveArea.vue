<script setup lang="ts">
/**
 * 对照 airi `components/InteractiveArea.vue` 的 DOM 结构：
 * 上：消息区（flex-1 overflow-hidden 滚动）
 * 下：工具条（发送方式、清空、图库、附件占位）+ `BasicTextarea` 同级样式的多行输入
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import {
  WS_PROTOCOL_NAME,
  createSunchatWs,
  type ServerMessage,
} from '@renderer/bridge/sunchat-ws'
import { postDesktopBus } from '@renderer/bridge/sunchat-desktop-bus'

const WS_LS = 'sunchat.wsUrl'

const defaultUrl =
  import.meta.env.VITE_SUNCHAT_WS_URL ?? 'ws://127.0.0.1:8000/ws'

function readWsLs(): string {
  try {
    return localStorage.getItem(WS_LS) ?? defaultUrl
  } catch {
    return defaultUrl
  }
}

type ChatRole = 'user' | 'assistant' | 'system' | 'error'

interface ChatLine {
  role: ChatRole
  text: string
}

const wsUrl = ref(readWsLs())
const connected = ref(false)
const entries = ref<ChatLine[]>([])
const streaming = ref('')
const messageInput = ref('')
const isComposing = ref(false)
const lastEnterTime = ref(0)
const DOUBLE_ENTER_INTERVAL_MS = 300
const TRAILING_NEWLINES_REGEX = /[\r\n]+$/

const SEND_MODES = ['enter', 'ctrl-enter', 'double-enter'] as const
type SendMode = (typeof SEND_MODES)[number]
const SEND_MODE_LS = 'ui/chat/settings/send-mode'

function readSendMode(): SendMode {
  try {
    const v = localStorage.getItem(SEND_MODE_LS) as SendMode | null
    if (v && SEND_MODES.includes(v)) return v
  } catch {
    /* ignore */
  }
  return 'enter'
}

const sendMode = ref<SendMode>(readSendMode())
watch(sendMode, (v) => {
  lastEnterTime.value = 0
  try {
    localStorage.setItem(SEND_MODE_LS, v)
  } catch {
    /* ignore */
  }
})

const sendModeLabels: Record<SendMode, string> = {
  'enter': '按 Enter 发送',
  'ctrl-enter': '按 Ctrl+Enter 发送',
  'double-enter': '双击 Enter 发送',
}

let client = createSunchatWs('', {})

watch(wsUrl, () => {
  try {
    localStorage.setItem(WS_LS, wsUrl.value)
  } catch {
    /* ignore */
  }
})

function pushEntry(role: ChatRole, text: string) {
  const t = text.trim()
  if (!t) return
  entries.value = [...entries.value, { role, text: t }]
}

function handleServerMessage(msg: ServerMessage) {
  if (msg.type === 'session') {
    const ok = msg.protocol.name === WS_PROTOCOL_NAME && msg.protocol.version === '1'
    pushEntry('system', `[session] ${msg.session_id} protocol ok=${ok}`)
    return
  }
  if (msg.type === 'emotion') {
    postDesktopBus({ type: 'emotion', mood_pct: msg.mood_pct, label: msg.label ?? null })
    return
  }
  if (msg.type === 'token') {
    streaming.value += msg.delta
    return
  }
  if (msg.type === 'done') {
    if (streaming.value.trim()) {
      pushEntry('assistant', streaming.value)
    }
    streaming.value = ''
    return
  }
  if (msg.type === 'error') {
    pushEntry('error', msg.message)
    streaming.value = ''
  }
}

function connect() {
  disconnect()
  client = createSunchatWs(wsUrl.value, {
    onOpen: () => {
      connected.value = true
      postDesktopBus({ type: 'connection', connected: true })
      pushEntry('system', `[open] ${wsUrl.value}`)
    },
    onClose: (ev) => {
      connected.value = false
      postDesktopBus({ type: 'connection', connected: false })
      pushEntry('system', `[close] code=${ev.code}`)
    },
    onError: () => {
      pushEntry('error', 'WebSocket error')
    },
    onMessage: handleServerMessage,
  })
  client.connect()
}

function disconnect() {
  client.disconnect()
  connected.value = false
  postDesktopBus({ type: 'connection', connected: false })
  streaming.value = ''
}

async function handleSend() {
  if (isComposing.value) return
  const t = messageInput.value.trim()
  if (!t || !connected.value) return
  messageInput.value = ''
  streaming.value = ''
  try {
    client.sendChat(t)
    pushEntry('user', t)
  } catch (e) {
    messageInput.value = t
    pushEntry('error', e instanceof Error ? e.message : String(e))
  }
}

function sendFromKeyboard() {
  messageInput.value = messageInput.value.replace(TRAILING_NEWLINES_REGEX, '')
  void handleSend()
}

function handleMessageInputKeydown(event: KeyboardEvent) {
  if (isComposing.value || event.key !== 'Enter') return

  const hasControl = event.ctrlKey || event.metaKey
  const hasShift = event.shiftKey

  switch (sendMode.value) {
    case 'enter':
      if (!hasShift && !hasControl) {
        event.preventDefault()
        sendFromKeyboard()
      }
      return
    case 'ctrl-enter':
      if (hasControl) {
        event.preventDefault()
        sendFromKeyboard()
      }
      return
    case 'double-enter':
      if (!hasShift && !hasControl) {
        const now = Date.now()
        if (now - lastEnterTime.value < DOUBLE_ENTER_INTERVAL_MS) {
          event.preventDefault()
          sendFromKeyboard()
          lastEnterTime.value = 0
        } else {
          lastEnterTime.value = now
        }
      }
  }
}

function cleanupChat() {
  entries.value = []
  streaming.value = ''
}

onMounted(() => {
  connect()
})

onBeforeUnmount(() => {
  disconnect()
})
</script>

<template>
  <div class="h-full w-full flex flex-col gap-1">
    <!-- SunChat：WS 配置条（airi 由 server channel 承担，此处等价能力） -->
    <div
      class="flex shrink-0 flex-col gap-2 border-b border-primary-900/25 pb-2"
    >
      <label class="text-10px text-neutral-500 uppercase tracking-wider">WebSocket</label>
      <input
        v-model="wsUrl"
        :disabled="connected"
        type="text"
        spellcheck="false"
        class="w-full border-2 border-primary-400/20 rounded-lg bg-primary-900/40 px-2 py-1.5 text-12px text-primary-100 outline-none focus:ring-2 focus:ring-primary-500/35"
      />
      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          :disabled="connected"
          class="rounded-md border-2 border-neutral-800/60 bg-neutral-800/70 px-3 py-1.5 text-12px text-neutral-200 backdrop-blur-md disabled:op-50 enabled:hover:bg-neutral-700/80"
          @click="connect"
        >
          连接
        </button>
        <button
          type="button"
          :disabled="!connected"
          class="rounded-md border-2 border-neutral-800/60 bg-neutral-800/70 px-3 py-1.5 text-12px text-neutral-200 backdrop-blur-md disabled:op-50 enabled:hover:bg-neutral-700/80"
          @click="disconnect"
        >
          断开
        </button>
        <span class="self-center text-11px text-primary-400/90">{{ connected ? '已连接' : '未连接' }}</span>
      </div>
    </div>

    <div class="min-h-0 w-full flex-1 overflow-y-auto pr-1">
      <div
        v-for="(m, i) in entries"
        :key="i"
        class="mb-3 max-w-full text-13px leading-relaxed"
        :class="{
          'text-primary-100': m.role === 'assistant',
          'text-neutral-300': m.role === 'user',
          'text-neutral-500': m.role === 'system',
          'text-red-400/90': m.role === 'error',
        }"
      >
        <span v-if="m.role === 'user'" class="mr-2 text-11px text-primary-500 font-medium">You</span>
        <span v-else-if="m.role === 'assistant'" class="mr-2 text-11px text-primary-400 font-medium">AI</span>
        <span class="whitespace-pre-wrap break-words">{{ m.text }}</span>
      </div>
      <div v-if="streaming" class="text-13px text-primary-200 leading-relaxed">
        <span class="mr-2 text-11px text-primary-400 font-medium">AI</span>
        {{ streaming }}<span class="op-50">▍</span>
      </div>
    </div>

    <!-- 对照 InteractiveArea：工具行 -->
    <div class="flex shrink-0 items-center justify-end gap-2 py-1">
      <select
        v-model="sendMode"
        class="max-h-[10lh] min-h-[1lh] max-w-52 cursor-pointer rounded-md border-0 bg-neutral-800 px-2 py-2 text-11px text-neutral-300 outline-none transition-transform active:scale-95"
        :title="'发送方式'"
      >
        <option v-for="mode in SEND_MODES" :key="mode" :value="mode">
          {{ sendModeLabels[mode] }}
        </option>
      </select>

      <button
        type="button"
        class="max-h-[10lh] min-h-[1lh] flex items-center justify-center rounded-md bg-neutral-800 p-2 text-lg text-neutral-400 outline-none transition-all active:scale-95 hover:text-red-400"
        title="清空记录"
        @click="cleanupChat"
      >
        🗑️
      </button>

      <button
        type="button"
        disabled
        class="max-h-[10lh] min-h-[1lh] flex items-center justify-center rounded-md bg-neutral-800 p-2 text-lg text-neutral-500 outline-none op-40"
        title="图库（预留）"
      >
        🖼️
      </button>

      <button
        type="button"
        disabled
        class="max-h-[10lh] min-h-[1lh] flex items-center justify-center rounded-md bg-neutral-800 p-2 text-lg text-neutral-500 outline-none op-40"
        title="附件（预留）"
      >
        📎
      </button>
    </div>

    <!-- 对照 `BasicTextarea` 外层 class 组合 -->
    <textarea
      v-model="messageInput"
      :disabled="!connected"
      rows="3"
      placeholder="消息…"
      class="ph-no-capture max-h-[10lh] min-h-[1lh] w-full shrink-0 resize-none overflow-y-auto border-2 border-primary-400/20 rounded-xl bg-primary-900/70 px-2 py-2 text-13px text-primary-100 font-medium outline-none transition-all placeholder:text-primary-300/80 disabled:op-50"
      @compositionstart="isComposing = true"
      @compositionend="isComposing = false"
      @keydown="handleMessageInputKeydown"
    />
  </div>
</template>
