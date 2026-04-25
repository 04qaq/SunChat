<script setup lang="ts">
/**
 * 对照 airi `pages/chat.vue`：`pt-11` 顶栏占位 + `WindowTitleBar` + `InteractiveArea`。
 */
import ChatInteractiveArea from '@renderer/components/sunchat/ChatInteractiveArea.vue'
import ChatWindowTitleBar from '@renderer/components/sunchat/ChatWindowTitleBar.vue'
</script>

<template>
  <div class="h-full w-full overflow-y-auto pt-11">
    <ChatWindowTitleBar title="Chat" />
    <ChatInteractiveArea
      class="interaction-area block h-full w-full p-4 transition-opacity duration-250"
    />
  </div>
</template>
