import { defineConfig, presetUno } from 'unocss'

/**
 * 参照 airi 舞台：深底、高饱和点缀（色相约 220°）、大圆角与轻边框。
 */
export default defineConfig({
  presets: [presetUno()],
  theme: {
    colors: {
      stage: {
        base: '#0b0b12',
        card: 'rgba(24, 26, 38, 0.72)',
        line: 'rgba(255,255,255,0.08)',
        accent: '#6b8cff',
        accent2: '#a78bfa',
        muted: '#8b8ba0',
      },
    },
  },
})
