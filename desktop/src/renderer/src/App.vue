<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'

const route = useRoute()

function minimize() {
  void window.desktop?.minimize()
}
function closeWin() {
  void window.desktop?.close()
}
</script>

<template>
  <!-- airi：Chat 为独立路由布局，无应用顶栏；主舞台保留 SunChat 顶栏 -->
  <div class="app-root flex h-full flex-col overflow-hidden">
    <template v-if="route.path !== '/chat'">
      <header
        class="titlebar flex h-9 shrink-0 items-center justify-between border-b border-neutral-800 px-2 pl-3"
      >
        <span
          class="text-12px text-neutral-100 font-600 tracking-wide"
          style="text-shadow: 0 0 24px hsl(var(--chromatic-hue) 70% 55% / 0.35)"
        >
          SunChat
        </span>
        <div class="titlebar-actions -mr-0.5 flex gap-0.5">
          <button type="button" class="tb-btn" @click="minimize">—</button>
          <button type="button" class="tb-btn tb-close" @click="closeWin">×</button>
        </div>
      </header>
    </template>
    <main
      class="main min-h-0 min-w-0 flex-1 overflow-hidden"
      :class="route.path === '/chat' ? 'flex flex-col' : 'p-0'"
    >
      <div
        class="h-full min-h-0 overflow-hidden"
        :class="route.path === '/chat' ? '' : 'rd-2xl'"
      >
        <RouterView />
      </div>
    </main>
  </div>
</template>
