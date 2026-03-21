import { keysToSnake, keysToCamel } from './common'

export type CaseConversionType = 'camelToSnake' | 'snakeToCamel'

/**
 * 转换对象键名
 * @param obj - 要转换的对象
 * @param type - 转换类型
 * @returns 转换后的对象
 * @deprecated 直接使用 keysToSnake 或 keysToCamel
 */
export function convertObjectKeys<T extends Record<string, unknown>>(
  obj: T,
  type: CaseConversionType
): Record<string, unknown> {
  return type === 'camelToSnake' ? keysToSnake(obj) : keysToCamel(obj)
}

export { keysToSnake, keysToCamel }
