<script setup lang="ts">
import { RouterView } from 'vue-router'

function minimize() {
  void window.desktop?.minimize()
}
function closeWin() {
  void window.desktop?.close()
}
</script>

<template>
  <div
    class="app-root flex flex-col h-full of-hidden bg-#0b0b12"
    style="background: radial-gradient(120% 80% at 50% -20%, rgba(99, 102, 241, 0.18), transparent), #0b0b12"
  >
    <header
      class="titlebar border-b border-white/6 flex h-9 shrink-0 items-center justify-between bg-black/30 px-2 pl-3 backdrop-blur-md"
    >
      <span
        class="text-12px font-600 text-white/95 tracking-wider"
        style="text-shadow: 0 0 20px rgba(99, 102, 241, 0.35)"
        >SunChat</span
      >
      <div class="titlebar-actions -mr-0.5 flex gap-0.5">
        <button type="button" class="tb-btn" @click="minimize">—</button>
        <button type="button" class="tb-btn tb-close" @click="closeWin">×</button>
      </div>
    </header>
    <main class="main of-hidden flex-1 min-h-0 p-0">
      <RouterView />
    </main>
  </div>
</template>
