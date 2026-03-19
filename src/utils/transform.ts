import { camelToSnake, snakeToCamel } from '@/utils'

export type CaseConversionType = 'camelToSnake' | 'snakeToCamel'

function convertKey(key: string, type: CaseConversionType): string {
  if (type === 'camelToSnake') {
    return camelToSnake(key)
  }
  return snakeToCamel(key)
}

export function convertObjectKeys<T extends Record<string, unknown>>(
  obj: T,
  type: CaseConversionType
): Record<string, unknown> {
  if (obj === null || typeof obj !== 'object') {
    return obj as Record<string, unknown>
  }

  if (Array.isArray(obj)) {
    return obj.map(item =>
      convertObjectKeys(item as Record<string, unknown>, type)
    ) as unknown as Record<string, unknown>
  }

  const result: Record<string, unknown> = {}
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const convertedKey = convertKey(key, type)
      const value = obj[key]
      result[convertedKey] =
        value !== null && typeof value === 'object'
          ? convertObjectKeys(value as Record<string, unknown>, type)
          : value
    }
  }
  return result
}
