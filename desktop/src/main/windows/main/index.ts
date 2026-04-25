import { app, BrowserWindow, shell } from 'electron'
import { join } from 'node:path'

import { transparentWindowConfig } from '../shared/window'

let mainWindow: BrowserWindow | null = null

export function getMainWindow(): BrowserWindow | null {
  return mainWindow
}

function mainDevUrl(): string | null {
  const base = process.env['ELECTRON_RENDERER_URL']
  if (!base) return null
  return `${base.replace(/\/?$/, '')}/#/`
}

export function createMainWindow(preloadPath: string, rendererIndexHtml: string): BrowserWindow {
  mainWindow = new BrowserWindow({
    width: 920,
    height: 640,
    minWidth: 640,
    minHeight: 420,
    title: 'SunChat',
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

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
    if (!app.isPackaged) {
      mainWindow?.webContents.openDevTools({ mode: 'detach' })
    }
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  const devUrl = mainDevUrl()
  if (devUrl) {
    void mainWindow.loadURL(devUrl)
  } else {
    void mainWindow.loadFile(rendererIndexHtml, { hash: '/' })
  }

  return mainWindow
}
