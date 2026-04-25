<script setup lang="ts">
/**
 * 对照 airi 主舞台：仅人物 + 右下角控制岛入口（打开独立 Chat 窗，见 `electronOpenChat`）。
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'

import Live2dStage from '@renderer/components/Live2dStage.vue'
import { subscribeDesktopBus } from '@renderer/bridge/sunchat-desktop-bus'

const modelUrl =
  import.meta.env.VITE_LIVE2D_MODEL ??
  '/live2d/models/sample-v3/sample-model-basic-series-v3.model3.json'

const lastMoodPct = ref(50)
const lastMoodLabel = ref<string | null>(null)
const remoteConnected = ref(false)

function openChat() {
  void window.desktop?.openChat()
}

let unsub: (() => void) | undefined

onMounted(() => {
  unsub = subscribeDesktopBus((msg) => {
    if (msg.type === 'emotion') {
      lastMoodPct.value = msg.mood_pct
      lastMoodLabel.value = msg.label ?? null
    }
    if (msg.type === 'connection') {
      remoteConnected.value = msg.connected
    }
  })
})

onBeforeUnmount(() => {
  unsub?.()
})

</script>

<template>
  <div class="relative h-full min-h-0 w-full overflow-hidden">
    <Live2dStage
      :model-json-url="modelUrl"
      :mood-pct="lastMoodPct"
      :mood-label="lastMoodLabel"
      class="absolute inset-0 z-0 h-full w-full"
    />

    <div
      class="pointer-events-none absolute right-3 top-3 z-10 flex items-center gap-2 border-2 border-neutral-800/50 rounded-full bg-neutral-800/70 px-2.5 py-1 text-10px text-neutral-300 backdrop-blur-md"
    >
      <span
        class="h-2 w-2 shrink-0 rounded-full"
        :class="remoteConnected ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]' : 'bg-neutral-600'"
      />
      <span class="hidden sm:inline">{{ remoteConnected ? '会话已连接' : '会话未连接' }}</span>
    </div>

    <!-- 对照 airi `controls-island/index.vue`：右下角入口 -->
    <div class="pointer-events-auto fixed bottom-2 right-2 z-20">
      <button
        type="button"
        class="flex items-center justify-center border-2 border-neutral-800/60 bg-neutral-800/70 p-2 backdrop-blur-md transition-all rd-xl hover:bg-neutral-700/80 active:scale-95"
        title="打开聊天"
        @click="openChat"
      >
        <span class="text-lg leading-none">💬</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* 舞台底透明，由 App 根渐变承担 */
</style>
