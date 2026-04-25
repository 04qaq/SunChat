import fs from 'node:fs'
import https from 'node:https'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const outDir = path.join(__dirname, '../src/renderer/public/live2d/core')
const outFile = path.join(outDir, 'live2dcubismcore.min.js')
const defaultUrl = 'https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js'
const root = path.resolve(__dirname, '..', '..')
const airiLayout = path.join(
  root,
  'third_party',
  'CubismSdkForWeb-5-r.3',
  'Core',
  'live2dcubismcore.min.js',
)

function tryCopyFile(from) {
  if (from && fs.existsSync(from)) {
    fs.mkdirSync(path.dirname(outFile), { recursive: true })
    fs.copyFileSync(from, outFile)
    console.log('[cubism-core] 已从本地复制', from)
    return true
  }
  return false
}

function tryFetch() {
  return new Promise((resolve, reject) => {
    fs.mkdirSync(path.dirname(outFile), { recursive: true })
    const file = fs.createWriteStream(outFile)
    const req = https.get(defaultUrl, (res) => {
      if (res.statusCode && res.statusCode >= 300) {
        res.resume()
        file.close()
        try {
          fs.unlinkSync(outFile)
        } catch { /* */ }
        reject(new Error(`HTTP ${res.statusCode}`))
        return
      }
      res.pipe(file)
      file.on('finish', () => {
        file.close()
        console.log('[cubism-core] 已下载', outFile)
        resolve()
      })
    })
    req.on('error', reject)
  })
}

if (fs.existsSync(outFile) && fs.statSync(outFile).size > 1000) {
  console.log('[cubism-core] 已存在，跳过', outFile)
  process.exit(0)
}

if (tryCopyFile(process.env['CUBISM_CORE_JS']?.trim() || null)) {
  process.exit(0)
}
if (tryCopyFile(airiLayout)) {
  process.exit(0)
}

tryFetch().catch((e) => {
  console.error('[cubism-core] 失败:', e.message)
  console.error('  请从 Live2D 官网下载 SDK，将 Core/live2dcubismcore.min.js 放到:')
  console.error(' ', outFile)
  process.exit(1)
})
