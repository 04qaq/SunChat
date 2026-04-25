import { BrowserWindow, app, ipcMain, shell } from 'electron'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { createMainWindow, getMainWindow } from './windows/main'
import { transparentWindowConfig } from './windows/shared/window'

const __dirname = dirname(fileURLToPath(import.meta.url))

const preloadPath = join(__dirname, '../preload/index.cjs')
const rendererIndexHtml = join(__dirname, '../renderer/index.html')

let chatWindow: BrowserWindow | null = null

function chatDevUrl(): string | null {
  const base = process.env['ELECTRON_RENDERER_URL']
  if (!base) return null
  return `${base.replace(/\/?$/, '')}/#/chat`
}

/**
 * 对照 airi `windows/chat/index.ts`：独立 Chat 窗体，加载 `#/chat`。
 */
function showChatWindow(): BrowserWindow {
  const existing = chatWindow && !chatWindow.isDestroyed() ? chatWindow : null
  if (existing) {
    if (existing.isMinimized()) existing.restore()
    existing.show()
    existing.focus()
    return existing
  }

  const win = new BrowserWindow({
    title: 'Chat',
    width: 600,
    height: 800,
    minWidth: 400,
    minHeight: 520,
    show: false,
    autoHideMenuBar: true,
    backgroundColor: '#0a0a0c',
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    ...transparentWindowConfig(),
  })

  chatWindow = win
  win.on('closed', () => {
    chatWindow = null
  })

  win.webContents.setWindowOpenHandler((details) => {
    void shell.openExternal(details.url)
    return { action: 'deny' }
  })

  const devUrl = chatDevUrl()
  if (devUrl) {
    void win.loadURL(devUrl)
  } else {
    void win.loadFile(rendererIndexHtml, { hash: '/chat' })
  }

  win.once('ready-to-show', () => {
    win.show()
  })

  return win
}

app.whenReady().then(() => {
  createMainWindow(preloadPath, rendererIndexHtml)
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow(preloadPath, rendererIndexHtml)
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

/** 对照 airi：由发起调用的窗口最小化/关闭 */
ipcMain.handle('window:minimize', (event) => {
  BrowserWindow.fromWebContents(event.sender)?.minimize()
})

ipcMain.handle('window:close', (event) => {
  BrowserWindow.fromWebContents(event.sender)?.close()
})

ipcMain.handle('app:open-chat', () => {
  showChatWindow()
})

/** @deprecated 仅兼容旧 preload；新代码请用 window:minimize */
ipcMain.handle('app:minimize', () => {
  getMainWindow()?.minimize()
})

/** @deprecated */
ipcMain.handle('app:close', () => {
  getMainWindow()?.close()
})
