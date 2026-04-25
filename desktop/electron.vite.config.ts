import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import { resolve } from 'node:path'

/**
 * 布局对照 airi `apps/stage-tamagotchi`：electron-vite 分 main / preload / renderer；
 * renderer 使用 `base: './'`，避免 production 以 file 协议加载时资源 404（见 airi 注释中 Maqsyo / issue #99）。
 * UnoCSS 与 airi 渲染层 @unocss 用法一致；Pixi 与 airi stage-ui-live2d 同栈需 dedupe。
 */
export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        output: { format: 'cjs' },
      },
    },
  },
  renderer: {
    base: './',
    resolve: {
      dedupe: ['pixi.js'],
      alias: { '@renderer': resolve('src/renderer/src') },
    },
    optimizeDeps: {
      include: ['pixi.js', 'pixi-live2d-display/cubism4'],
    },
    plugins: [vue(), UnoCSS()],
  },
})
