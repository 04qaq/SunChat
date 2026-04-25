<script setup lang="ts">
/**
 * 对照 airi `components/Window/TitleBar.vue`：顶栏 `drag-region`、neutral 底、图标+标题。
 * 子窗口增加最小化/关闭（无系统标题栏时必需）。
 */
defineProps<{
  title: string
}>()

const platform = window.desktop?.platform ?? 'win32'

function minimize() {
  void window.desktop?.minimize()
}
function closeWin() {
  void window.desktop?.close()
}
</script>

<template>
  <div
    class="drag-region fixed left-0 top-0 z-100 w-full flex select-none items-center gap-2 border-b border-neutral-800 bg-neutral-900 py-2 pr-2"
    :class="platform === 'darwin' ? 'pl-20' : 'pl-3'"
  >
    <div class="drag-region flex min-w-0 flex-1 cursor-default items-center gap-2 rounded-md px-1.5 py-0.5 transition-colors hover:bg-neutral-800">
      <span class="shrink-0 text-base leading-none" aria-hidden="true">💬</span>
      <span class="truncate text-sm text-neutral-100 whitespace-nowrap">{{ title }}</span>
    </div>
    <div class="no-drag flex shrink-0 items-center gap-0.5">
      <button
        type="button"
        class="rounded-md px-2.5 py-1 text-sm text-neutral-500 transition-colors hover:bg-neutral-800 hover:text-neutral-200"
        aria-label="最小化"
        @click="minimize"
      >
        —
      </button>
      <button
        type="button"
        class="rounded-md px-2.5 py-1 text-sm text-neutral-500 transition-colors hover:bg-red-600 hover:text-white"
        aria-label="关闭"
        @click="closeWin"
      >
        ×
      </button>
    </div>
  </div>
</template>
