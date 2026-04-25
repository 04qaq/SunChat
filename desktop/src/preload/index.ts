import { contextBridge, ipcRenderer } from 'electron'

/**
 * airi 在 preload 中通过 `contextBridge` 挂 `electron` + `platform`（见 airi `preload/shared.ts`）；
 * SunChat 自研为 `desktop` 命名空间，避免与页面全局冲突。
 */
contextBridge.exposeInMainWorld('desktop', {
  platform: process.platform,
  versions: {
    electron: process.versions.electron,
    chrome: process.versions.chrome,
  },
  minimize: () => ipcRenderer.invoke('app:minimize'),
  close: () => ipcRenderer.invoke('app:close'),
})
