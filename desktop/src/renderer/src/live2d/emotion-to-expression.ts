/**
 * 将 mood_pct / 可选 label 映射到示例模型 `sample-model-basic-series-v3` 中的表情名。
 * 与 airi emotion 常量不必一致，仅服务本仓库模型。
 */
export function pickExpressionName(moodPct: number, label?: string | null): string | null {
  const l = (label || '').toLowerCase()
  if (l.includes('namida') || l.includes('泪') || moodPct < 22) {
    return '06.eye_namida'
  }
  if (l.includes('heart') || l.includes('kirakira') || moodPct > 78) {
    return l.includes('heart') ? '04.eye_heart' : '05.eye_kirakira'
  }
  if (l.includes('bikkuri') || l.includes('惊')) {
    return '03.eye_bikkuri'
  }
  if (moodPct > 55) {
    return '01.eye_smile'
  }
  if (moodPct < 35) {
    return '02.eye_tojiru'
  }
  return null
}
