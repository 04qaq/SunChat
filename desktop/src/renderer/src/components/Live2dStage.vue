<script setup lang="ts">
import '@pixi/unsafe-eval'

import { Application, Ticker } from 'pixi.js'
import { Live2DModel as Live2DModelClass } from 'pixi-live2d-display/cubism4'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { applyCubism4FaceWorkaround } from '@renderer/live2d/cubism-face'
import { pickExpressionName } from '@renderer/live2d/emotion-to-expression'

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
}>()

const hostRef = ref<HTMLDivElement | null>(null)
const status = ref<'idle' | 'loading' | 'ready' | 'error'>('idle')
const errText = ref('')

type Live2DModelInstance = InstanceType<typeof Live2DModelClass>

let app: Application | null = null
let model: Live2DModelInstance | null = null
let ro: ResizeObserver | null = null

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
  m.x = w / 2
  m.y = h * 0.55
  const scale = Math.min((w * 0.72) / m.width, (h * 0.88) / m.height) * 0.9
  m.scale.set(scale)
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
  el.appendChild(canvas)
  app = nextApp

  try {
    const url = resolveModelUrl(props.modelJsonUrl)
    const m = await Live2DModelClass.from(url, {
      autoHitTest: false,
    })
    model = m
    applyCubism4FaceWorkaround(m)
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
  if (model) {
    try {
      model.destroy()
    } catch { /* */ }
  }
  model = null
  if (app) {
    try {
      app.destroy(true)
    } catch { /* */ }
  }
  app = null
}

onMounted(() => {
  const el = hostRef.value
  if (!el) return
  void boot()
  ro = new ResizeObserver(() => {
    if (!app || !hostRef.value) return
    const w = Math.max(64, hostRef.value.clientWidth)
    const h = Math.max(64, hostRef.value.clientHeight)
    const r = 2
    app.renderer.resize(w * r, h * r)
    app.stage.scale.set(r)
    layoutModel(w, h)
  })
  ro.observe(el)
})

onBeforeUnmount(() => {
  teardown()
})

watch(
  () => [props.moodPct, props.moodLabel] as const,
  () => applyExpressionFromMood(),
)

defineExpose({ applyExpressionFromMood })
</script>

<template>
  <div class="live2d-wrap relative h-full w-full min-h-48">
    <div
      ref="hostRef"
      class="live2d-host h-full w-full overflow-hidden rd-2xl"
      :aria-label="'Live2D'"
    />
    <p
      v-if="status === 'loading'"
      class="pointer-events-none absolute bottom-2 left-2 text-11px text-zinc-400/80"
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
.live2d-host {
  position: relative;
  background: radial-gradient(ellipse 100% 85% at 50% 100%, rgba(99, 102, 241, 0.14), transparent 55%),
    linear-gradient(165deg, rgba(32, 36, 58, 0.55) 0%, rgba(12, 12, 22, 0.2) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.2) inset, 0 24px 48px rgba(0, 0, 0, 0.25);
}
</style>
