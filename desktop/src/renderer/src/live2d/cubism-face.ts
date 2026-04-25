/**
 * 部分环境下面部/眼睛层异常时做保守参数修正（思路同历史 SunChat 桌面适配）。
 */
export function applyCubism4FaceWorkaround(
  model: { internalModel?: unknown } | null,
): void {
  if (!model?.internalModel) return
  const im = model.internalModel as { renderer?: { useHighPrecisionMask?: boolean } }
  try {
    if (im.renderer && 'useHighPrecisionMask' in im.renderer) {
      im.renderer.useHighPrecisionMask = true
    }
  } catch { /* */ }
  const core = (model.internalModel as { coreModel?: { setParameterValueById?: (id: string, v: number) => void } })
    .coreModel
  try {
    core?.setParameterValueById?.('ParamEyeLOpen', 1)
    core?.setParameterValueById?.('ParamEyeROpen', 1)
  } catch { /* */ }
}
