import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..', '..')
const src = path.join(
  root,
  'sample-model-basic-series-v3_vts',
  'sample-model-basic-series-v3_vts',
)
const dest = path.join(
  __dirname,
  '../src/renderer/public/live2d/models/sample-v3',
)

function copyRecursive(from, to) {
  if (!fs.existsSync(from)) {
    return false
  }
  fs.mkdirSync(to, { recursive: true })
  for (const name of fs.readdirSync(from, { withFileTypes: true })) {
    const s = path.join(from, name.name)
    const d = path.join(to, name.name)
    if (name.isDirectory()) {
      copyRecursive(s, d)
    } else {
      fs.copyFileSync(s, d)
    }
  }
  return true
}

if (!fs.existsSync(src)) {
  console.warn('[sync-live2d] 跳过：未找到示例模型', src)
  console.warn('  确认已将 sample-model-basic-series-v3_vts 放在仓库根目录。')
} else if (copyRecursive(src, dest)) {
  console.log('[sync-live2d] 已同步 →', dest)
}
