<script setup lang="ts">
import '@pixi/unsafe-eval'

import type { FederatedPointerEvent } from 'pixi.js'
import { Application, Ticker } from 'pixi.js'
import { Live2DModel as Live2DModelClass } from 'pixi-live2d-display/cubism4'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { applyCubism4FaceWorkaround } from '@renderer/live2d/cubism-face'
import { pickExpressionName } from '@renderer/live2d/emotion-to-expression'

const ZOOM_MIN = 0.3
const ZOOM_MAX = 2

const props = withDefaults(
  defineProps<{
    modelJsonUrl: string
    moodPct?: number
    moodLabel?: string | null
  }>(),
  {
    moodPct: 50,
    moodLabel: null,
  },
)

const emit = defineEmits<{
  ready: []
  error: [Error]
  avatarClick: []
}>()

const hostRef = ref<HTMLDivElement | null>(null)
const status = ref<'idle' | 'loading' | 'ready' | 'error'>('idle')
const errText = ref('')

const userScaleMul = ref(1)
const panX = ref(0)
const panY = ref(0)

type Live2DModelInstance = InstanceType<typeof Live2DModelClass>

let app: Application | null = null
let model: Live2DModelInstance | null = null
let ro: ResizeObserver | null = null
let panDrag = false
let panLast = { x: 0, y: 0 }

function publicBase(): string {
  return new URL('./', window.location.href).toString()
}

function resolveModelUrl(path: string): string {
  return new URL(path.replace(/^\//, ''), publicBase()).toString()
}

function layoutModel(w: number, h: number) {
  if (!model) return
  const m = model
  m.anchor.set(0.5, 0.5)
  const baseScale = Math.min((w * 0.72) / m.width, (h * 0.88) / m.height) * 0.9
  m.scale.set(baseScale * userScaleMul.value)
  m.x = w / 2 + panX.value
  m.y = h * 0.55 + panY.value
}

function relayoutFromHost() {
  const el = hostRef.value
  if (!el || !app) return
  const w = Math.max(64, el.clientWidth)
  const h = Math.max(64, el.clientHeight)
  const r = 2
  app.renderer.resize(w * r, h * r)
  app.stage.scale.set(r)
  layoutModel(w, h)
}

function applyExpressionFromMood() {
  if (!model || status.value !== 'ready') return
  const name = pickExpressionName(props.moodPct ?? 50, props.moodLabel)
  if (name) {
    void model.expression(name)
  }
}

function playIdleMotion() {
  if (!model) return
  void model.motion('' as string)
}

function onModelPointerDown(e: FederatedPointerEvent) {
  if (!(e.ctrlKey || e.metaKey)) return
  panDrag = true
  panLast = { x: e.global.x, y: e.global.y }
}

function onStagePointerMove(e: FederatedPointerEvent) {
  if (!panDrag) return
  const dx = e.global.x - panLast.x
  const dy = e.global.y - panLast.y
  panLast = { x: e.global.x, y: e.global.y }
  const el = hostRef.value
  if (!el) return
  const r = 2
  panX.value += dx / r
  panY.value += dy / r
  relayoutFromHost()
}

function endPan() {
  panDrag = false
}

function onModelPointerTap(e: FederatedPointerEvent) {
  if (e.button !== 0) return
  if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return
  emit('avatarClick')
}

function onWheelHost(e: WheelEvent) {
  const el = hostRef.value
  if (!el) return
  const delta = e.deltaY
  const factor = delta < 0 ? 1.08 : 1 / 1.08
  userScaleMul.value = Math.min(
    ZOOM_MAX,
    Math.max(ZOOM_MIN, userScaleMul.value * factor),
  )
  relayoutFromHost()
}

function resetZoomAndPan() {
  userScaleMul.value = 1
  panX.value = 0
  panY.value = 0
  relayoutFromHost()
}

function centerPanOnly() {
  panX.value = 0
  panY.value = 0
  relayoutFromHost()
}

async function boot() {
  const el = hostRef.value
  if (!el) return
  if (typeof (window as { Live2DCubismCore?: unknown }).Live2DCubismCore === 'undefined') {
    const msg = '未加载 live2dcubismcore：请执行 npm run sync:assets'
    errText.value = msg
    status.value = 'error'
    emit('error', new Error(msg))
    return
  }

  status.value = 'loading'
  errText.value = ''
  const w = Math.max(64, el.clientWidth)
  const h = Math.max(64, el.clientHeight)
  const res = 2

  Live2DModelClass.registerTicker(Ticker)

  const nextApp = new Application({
    width: w * res,
    height: h * res,
    backgroundAlpha: 0,
    antialias: true,
    autoDensity: false,
    resolution: 1,
  })
  const canvas = nextApp.view as HTMLCanvasElement
  canvas.style.width = '100%'
  canvas.style.height = '100%'
  canvas.style.objectFit = 'cover'
  canvas.style.display = 'block'
  nextApp.stage.scale.set(res)
  nextApp.stage.eventMode = 'passive'
  el.appendChild(canvas)
  app = nextApp

  try {
    const url = resolveModelUrl(props.modelJsonUrl)
    const m = await Live2DModelClass.from(url, {
      autoHitTest: true,
    })
    model = m
    applyCubism4FaceWorkaround(m)
    m.eventMode = 'static'
    m.cursor = 'pointer'
    m.on('pointerdown', onModelPointerDown)
    m.on('pointertap', onModelPointerTap)
    nextApp.stage.on('pointermove', onStagePointerMove)
    nextApp.stage.on('pointerup', endPan)
    nextApp.stage.on('pointerupoutside', endPan)
    nextApp.stage.addChild(m)
    layoutModel(w, h)
    applyExpressionFromMood()
    queueMicrotask(() => playIdleMotion())
    status.value = 'ready'
    emit('ready')
  } catch (e) {
    const err = e instanceof Error ? e : new Error(String(e))
    errText.value = err.message
    status.value = 'error'
    emit('error', err)
  }
}

function teardown() {
  ro?.disconnect()
  ro = null
  window.removeEventListener('pointerup', endPan)
  if (app) {
    try {
      app.stage.off('pointermove', onStagePointerMove)
      app.stage.off('pointerup', endPan)
      app.stage.off('pointerupoutside', endPan)
    } catch {
      /* */
    }
  }
  if (model) {
    try {
      model.off('pointerdown', onModelPointerDown)
      model.off('pointertap', onModelPointerTap)
      model.destroy()
    } catch {
      /* */
    }
  }
  model = null
  if (app) {
    try {
      app.destroy(true)
    } catch {
      /* */
    }
  }
  app = null
}

onMounted(() => {
  const el = hostRef.value
  if (!el) return
  void boot()
  window.addEventListener('pointerup', endPan)
  ro = new ResizeObserver(() => relayoutFromHost())
  ro.observe(el)
})

onBeforeUnmount(() => {
  teardown()
})

watch(
  () => [props.moodPct, props.moodLabel] as const,
  () => applyExpressionFromMood(),
)

defineExpose({
  resetZoomAndPan,
  centerPanOnly,
})
</script>

<template>
  <div class="live2d-wrap relative h-full min-h-48 w-full" @wheel.prevent="onWheelHost">
    <!-- 对照 airi `pages/index.vue` 舞台容器：`rounded-2xl overflow-hidden` -->
    <div
      ref="hostRef"
      class="live2d-host h-full w-full overflow-hidden rd-2xl"
      :aria-label="'Live2D'"
    />
    <p
      v-if="status === 'loading'"
      class="pointer-events-none absolute bottom-2 left-2 text-11px text-neutral-400/90"
    >
      加载模型…
    </p>
    <p
      v-if="status === 'error'"
      class="absolute bottom-2 left-2 right-2 break-all text-11px text-rose-400/95"
    >
      {{ errText }}
    </p>
  </div>
</template>

<script lang="ts">
declare global {
  interface Window {
    Live2DCubismCore?: unknown
  }
}
</script>

<style scoped>
/* 对照 airi 舞台默认氛围：中性底 + 底部轻 primary 晕（色相同 `uno.config` chromatic） */
.live2d-host {
  position: relative;
  background:
    radial-gradient(ellipse 100% 88% at 50% 100%, hsl(220.44 55% 45% / 0.12), transparent 55%),
    linear-gradient(165deg, rgba(23, 23, 27, 0.45) 0%, rgba(10, 10, 12, 0.2) 100%);
}
</style>
