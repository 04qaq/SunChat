import { contextBridge, ipcRenderer } from 'electron'

/**
 * 对照 airi `preload`：`window` 级最小化/关闭由发起窗口处理（`window:*`）。
 * `app:open-chat` 对应 airi `electronOpenChat` invoke。
 */
contextBridge.exposeInMainWorld('desktop', {
  platform: process.platform,
  versions: {
    electron: process.versions.electron,
    chrome: process.versions.chrome,
  },
  minimize: () => ipcRenderer.invoke('window:minimize'),
  close: () => ipcRenderer.invoke('window:close'),
  openChat: () => ipcRenderer.invoke('app:open-chat'),
})
