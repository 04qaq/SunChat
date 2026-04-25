<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

import Live2dStage from '@renderer/components/Live2dStage.vue'
import {
  WS_PROTOCOL_NAME,
  createSunchatWs,
  type ServerMessage,
} from '@renderer/bridge/sunchat-ws'

const modelUrl =
  import.meta.env.VITE_LIVE2D_MODEL ??
  '/live2d/models/sample-v3/sample-model-basic-series-v3.model3.json'

const defaultUrl =
  import.meta.env.VITE_SUNCHAT_WS_URL ?? 'ws://127.0.0.1:8000/ws'

const wsUrl = ref(defaultUrl)
const connected = ref(false)
const logLines = ref<string[]>([])
const input = ref('')
const streaming = ref('')
const sessionId = ref<string | null>(null)
const protocolOk = ref<boolean | null>(null)
const lastMoodPct = ref(50)
const lastMoodLabel = ref<string | null>(null)

let client = createSunchatWs('', {})

const statusText = computed(() => {
  if (!connected.value) return '未连接'
  if (protocolOk.value === false) return '已连接（协议版本不一致）'
  return '已连接'
})

function pushLog(line: string) {
  logLines.value = [...logLines.value, line].slice(-200)
}

function handleServerMessage(msg: ServerMessage) {
  if (msg.type === 'session') {
    sessionId.value = msg.session_id
    const p = msg.protocol
    protocolOk.value =
      p.name === WS_PROTOCOL_NAME && p.version === '1'
    pushLog(
      `[session] ${msg.session_id} protocol=${p.name}@${p.version} ok=${protocolOk.value}`,
    )
    return
  }
  if (msg.type === 'emotion') {
    lastMoodPct.value = msg.mood_pct
    lastMoodLabel.value = msg.label ?? null
    pushLog(`[emotion] mood=${msg.mood_pct}` + (msg.label ? ` label=${msg.label}` : ''))
    return
  }
  if (msg.type === 'token') {
    streaming.value += msg.delta
    return
  }
  if (msg.type === 'done') {
    if (streaming.value) {
      pushLog(`[assistant] ${streaming.value}`)
    }
    streaming.value = ''
    return
  }
  if (msg.type === 'error') {
    pushLog(`[error] ${msg.message}`)
    streaming.value = ''
  }
}

function connect() {
  disconnect()
  client = createSunchatWs(wsUrl.value, {
    onOpen: () => {
      connected.value = true
      sessionId.value = null
      protocolOk.value = null
      pushLog(`[open] ${wsUrl.value}`)
    },
    onClose: (ev) => {
      connected.value = false
      pushLog(`[close] code=${ev.code} reason=${ev.reason || ''}`)
    },
    onError: () => {
      pushLog('[error] WebSocket error')
    },
    onMessage: handleServerMessage,
  })
  client.connect()
}

function disconnect() {
  client.disconnect()
  connected.value = false
  streaming.value = ''
}

function send() {
  const t = input.value.trim()
  if (!t || !connected.value) return
  try {
    streaming.value = ''
    client.sendChat(t)
    pushLog(`[user] ${t}`)
    input.value = ''
  } catch (e) {
    pushLog(`[send] ${e instanceof Error ? e.message : String(e)}`)
  }
}

onBeforeUnmount(() => {
  disconnect()
})
</script>

<template>
  <div
    class="home grid h-full min-h-0 grid-cols-1 gap-0 lg:grid-cols-[1fr_minmax(280px,360px)]"
  >
    <section
      class="stage-area relative min-h-[11rem] border-white/5 border-b lg:min-h-0 lg:border-r lg:border-b-0"
    >
      <Live2dStage
        :model-json-url="modelUrl"
        :mood-pct="lastMoodPct"
        :mood-label="lastMoodLabel"
        class="h-full w-full"
      />
      <p
        class="pointer-events-none absolute left-3 top-2 rounded-md bg-black/32 px-2 py-0.5 text-10px text-white/50 backdrop-blur-sm"
      >
        Live2D · sample
      </p>
    </section>

    <section
      class="chat-shell flex min-h-0 min-w-0 flex-col gap-0 border-t border-white/5 bg-black/25 p-3 backdrop-blur-sm lg:border-t-0"
    >
      <div class="mb-2 shrink-0">
        <p class="mb-0.5 text-11px text-white/40 uppercase tracking-wider">WebSocket</p>
        <div class="flex flex-wrap items-center gap-2">
          <input
            v-model="wsUrl"
            :disabled="connected"
            type="text"
            class="min-w-0 flex-1 border border-white/10 rounded-lg bg-zinc-900/80 px-2.5 py-1.5 text-12px text-zinc-100 outline-none ring-violet-500/40 focus:ring-2"
            spellcheck="false"
          />
          <button
            type="button"
            :disabled="connected"
            class="rounded-lg border border-white/12 bg-white/5 px-3 py-1.5 text-12px text-zinc-200 enabled:hover:bg-white/10 disabled:op-50"
            @click="connect"
          >
            连接
          </button>
          <button
            type="button"
            :disabled="!connected"
            class="rounded-lg border border-white/12 bg-white/5 px-3 py-1.5 text-12px text-zinc-200 enabled:hover:bg-white/10 disabled:op-50"
            @click="disconnect"
          >
            断开
          </button>
        </div>
        <p class="mt-1.5 text-11px text-violet-300/80">
          {{ statusText }}
          <span v-if="sessionId" class="ml-2 font-mono text-white/35">{{ sessionId.slice(0, 8) }}…</span>
        </p>
      </div>

      <div
        class="transcript min-h-[7.5rem] flex-1 of-y-auto of-x-hidden border border-white/8 rounded-xl bg-zinc-950/50 p-2 text-12px text-zinc-200 leading-relaxed"
        aria-live="polite"
      >
        <p v-for="(line, i) in logLines" :key="i" class="m-0 mb-1 break-words whitespace-pre-wrap">
          {{ line }}
        </p>
        <p v-if="streaming" class="m-0 text-violet-200/80">
          {{ streaming }}<span class="op-50">▍</span>
        </p>
        <p v-if="!logLines.length && !streaming" class="m-0 text-zinc-500">连接后可对话；情绪会驱动侧栏 Live2D 表情。</p>
      </div>

      <div class="mt-2 flex min-h-0 shrink-0 gap-2">
        <textarea
          v-model="input"
          :disabled="!connected"
          class="min-h-14 flex-1 resize-y border border-white/10 rounded-xl bg-zinc-900/70 px-3 py-2 text-13px text-zinc-100 placeholder:text-zinc-500 outline-none max-h-32 focus:ring-2 focus:ring-violet-500/35 disabled:op-50"
          placeholder="消息… Enter 发送，Shift+Enter 换行"
          @keydown.enter.exact.prevent="send"
        />
        <button
          type="button"
          :disabled="!connected"
          class="self-end border-0 rounded-xl bg-violet-500/90 px-4 py-2 text-12px text-white font-medium shadow-md enabled:hover:bg-violet-500 disabled:op-40"
          @click="send"
        >
          发送
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  background: linear-gradient(180deg, rgba(20, 22, 35, 0.4) 0%, transparent 40%);
}
</style>
