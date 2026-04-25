import { app, BrowserWindow, ipcMain } from 'electron'
import { createMainWindow, getMainWindow } from './windows/main'

app.whenReady().then(() => {
  createMainWindow()
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

ipcMain.handle('app:minimize', () => {
  getMainWindow()?.minimize()
})

ipcMain.handle('app:close', () => {
  getMainWindow()?.close()
})
