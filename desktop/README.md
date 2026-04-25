# SunChat 桌面端

- **技术栈**：参照 [airi `stage-tamagotchi`](https://github.com/moeru-ai/airi) 的 **electron-vite 三端**、**`base: './'`**；**UnoCSS**（@unocss/reset + 工具类）、**Vue 3**、vue-router、Pinia。Live2D 使用与 airi `stage-ui-live2d` 相同的 **Pixi 7 + `pixi-live2d-display/cubism4` + 先行加载 `live2dcubismcore.min.js`（见 `index.html`）**。
- **资源**：`npm run sync:assets` 会将仓库根目录 `sample-model-basic-series-v3_vts/...` 同步到 `public/live2d/models/sample-v3/`，并拉取/复制 **Cubism Core** 到 `public/live2d/core/`（可设 `CUBISM_CORE_JS` 指向本地 SDK 文件避免下载）。
- **联调**：先 `uv run sunchat`（默认 `ws://127.0.0.1:8000/ws`），再 `npm run dev`。可配置 `VITE_SUNCHAT_WS_URL`、`VITE_LIVE2D_MODEL`（见 `.env.example`）。

## 命令

```bash
cd desktop
npm install
npm run sync:assets
npm run dev
```

在仓库根目录也可：`npm run dev:desktop`（见根 `package.json`）。首次或模型更新后请执行 `sync:assets`。

## 协议

与 `sunchat.api.ws_protocol` 及 `ws_session` 的 JSON 一致；桥接在 `src/renderer/src/bridge/sunchat-ws.ts`。**`emotion` 消息**的 `mood_pct` / `label` 会驱动侧栏 Live2D 表情（`live2d/emotion-to-expression.ts` 映射到示例模型表情名）。

整体策略见 `docs/DESKTOP_AIRI_PORTING.md`。
