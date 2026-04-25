/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUNCHAT_WS_URL?: string
  readonly VITE_LIVE2D_MODEL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare global {
  interface Window {
    desktop?: {
      platform: string
      versions: { electron: string; chrome: string }
      minimize: () => Promise<void>
      close: () => Promise<void>
    }
  }
}

export {}
