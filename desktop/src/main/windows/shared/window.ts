import type { BrowserWindowConstructorOptions } from 'electron'

/** 与 airi `transparentWindowConfig` 同型：无边框透明主窗常用基底。 */
export function transparentWindowConfig(): BrowserWindowConstructorOptions {
  return {
    frame: false,
    titleBarStyle: process.platform === 'darwin' ? 'hidden' : undefined,
    transparent: true,
    hasShadow: false,
  }
}
