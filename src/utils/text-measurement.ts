/**
 * 文本测量工具
 *
 * 基于 Pretext 库实现，用于预计算文本高度
 * 避免昂贵的 DOM 测量操作
 */

import { prepare, layout } from '@chenglou/pretext'

export interface TextMeasurementConfig {
  /**
   * 字体配置，与 Canvas 2D context.font 格式一致
   * @default '16px Inter, system-ui, sans-serif'
   */
  font: string

  /**
   * 行高
   * @default 24
   */
  lineHeight: number

  /**
   * 空白字符处理方式
   * @default 'normal'
   */
  whiteSpace?: 'normal' | 'pre-wrap'
}

const DEFAULT_CONFIG: TextMeasurementConfig = {
  font: '16px Inter, system-ui, sans-serif',
  lineHeight: 24,
  whiteSpace: 'normal',
}

/**
 * 文本测量结果缓存
 */
interface CachedMeasurement {
  prepared: ReturnType<typeof prepare>
  lastMeasuredWidth: number
  lastHeight: number
  lastLineCount: number
}

const measurementCache = new Map<string, CachedMeasurement>()

/**
 * 生成缓存键
 */
function getCacheKey(text: string, config: TextMeasurementConfig): string {
  return `${text}::${config.font}::${config.whiteSpace || 'normal'}`
}

/**
 * 测量文本高度
 *
 * @param text - 要测量的文本
 * @param maxWidth - 最大宽度（像素）
 * @param config - 测量配置
 * @returns 高度和行数信息
 */
export function measureTextHeight(
  text: string,
  maxWidth: number,
  config?: Partial<TextMeasurementConfig>
): { height: number; lineCount: number } {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config }
  const cacheKey = getCacheKey(text, mergedConfig)

  let cached = measurementCache.get(cacheKey)

  // 如果没有缓存或文本变化，重新 prepare
  if (!cached) {
    const prepared = prepare(text, mergedConfig.font, {
      whiteSpace: mergedConfig.whiteSpace,
    })
    cached = {
      prepared,
      lastMeasuredWidth: -1,
      lastHeight: 0,
      lastLineCount: 0,
    }
    measurementCache.set(cacheKey, cached)
  }

  // 如果宽度相同，直接返回缓存的结果
  if (cached.lastMeasuredWidth === maxWidth) {
    return {
      height: cached.lastHeight,
      lineCount: cached.lastLineCount,
    }
  }

  // 使用 layout 计算高度（纯算术运算，非常快）
  const result = layout(cached.prepared, maxWidth, mergedConfig.lineHeight)

  // 更新缓存
  cached.lastMeasuredWidth = maxWidth
  cached.lastHeight = result.height
  cached.lastLineCount = result.lineCount

  return result
}

/**
 * 清空测量缓存
 * 当字体配置变化时调用
 */
export function clearMeasurementCache(): void {
  measurementCache.clear()
}

/**
 * 创建一个文本测量器实例
 * 便于在组件中使用
 */
export function createTextMeasurer(config?: Partial<TextMeasurementConfig>) {
  const instanceConfig = { ...DEFAULT_CONFIG, ...config }

  return {
    measure: (text: string, maxWidth: number) => measureTextHeight(text, maxWidth, instanceConfig),
    clearCache: clearMeasurementCache,
    updateConfig: (newConfig: Partial<TextMeasurementConfig>) => {
      Object.assign(instanceConfig, newConfig)
      clearMeasurementCache()
    },
  }
}
