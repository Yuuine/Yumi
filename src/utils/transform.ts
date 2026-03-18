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

export function toSnakeCase<T extends Record<string, unknown>>(obj: T): Record<string, unknown> {
  return convertObjectKeys(obj, 'camelToSnake')
}

export function toCamelCase<T extends Record<string, unknown>>(obj: T): Record<string, unknown> {
  return convertObjectKeys(obj, 'snakeToCamel')
}

export function pickFields<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> {
  const result = {} as Pick<T, K>
  for (const key of keys) {
    if (key in obj) {
      result[key] = obj[key]
    }
  }
  return result
}

export function omitFields<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> {
  const result = { ...obj }
  for (const key of keys) {
    delete result[key]
  }
  return result as Omit<T, K>
}
