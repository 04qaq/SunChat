import { defineConfig, presetUno, transformerVariantGroup } from 'unocss'

/**
 * 对照 airi 根目录 `uno.config.ts`：
 * - `presetChromatic` 的 `baseHue: 220.44` → primary 用同色相 HSL（SunChat 不引入 @proj-airi/unocss-preset-chromatic）
 * - 舞台与岛台大量使用 `neutral-*` + `backdrop-blur`（见 `control-button.vue`、`controls-island/index.vue`）
 */
export default defineConfig({
  presets: [presetUno()],
  transformers: [transformerVariantGroup()],
  theme: {
    colors: {
      primary: {
        DEFAULT: 'hsl(220 65% 52%)',
        50: 'hsl(220 100% 97%)',
        100: 'hsl(220 95% 94%)',
        200: 'hsl(220 90% 86%)',
        300: 'hsl(220 80% 74%)',
        400: 'hsl(220 75% 64%)',
        500: 'hsl(220 65% 52%)',
        600: 'hsl(220 60% 44%)',
        700: 'hsl(220 55% 36%)',
        800: 'hsl(220 50% 28%)',
        900: 'hsl(220 45% 20%)',
      },
    },
  },
})
