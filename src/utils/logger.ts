/**
 * Logging System - 前端结构化日志系统
 *
 * 支持：
 * - 统一日志格式
 * - 日志级别控制
 * - 敏感信息过滤
 * - Tauri 原生日志集成
 */

import { ref, computed } from 'vue'

export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR'

interface LogEntry {
  timestamp: string
  level: LogLevel
  module: string
  message: string
  data?: Record<string, unknown>
  error?: Error
}

interface LoggerConfig {
  level: LogLevel
  enableConsole: boolean
  enableFile: boolean
  maxEntries: number
}

const LOG_LEVELS: Record<LogLevel, number> = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
}

const SENSITIVE_PATTERNS: Array<[RegExp, string]> = [
  [
    /(api[_-]?key|apikey|token|secret|password|pwd)['"]?\s*[:=]\s*['"]?([^'"\s,}]+)/gi,
    '$1=***REDACTED***',
  ],
  [/(Bearer\s+)[A-Za-z0-9\-._~+/]+=*/gi, '$1***REDACTED***'],
  [/(sk-[a-zA-Z0-9]{20,})/g, 'sk-***REDACTED***'],
]

function filterSensitiveInfo(message: string): string {
  let result = message
  for (const [pattern, replacement] of SENSITIVE_PATTERNS) {
    result = result.replace(pattern, replacement)
  }
  return result
}

function filterObjectSensitive(obj: unknown): unknown {
  if (typeof obj === 'string') {
    return filterSensitiveInfo(obj)
  }
  if (Array.isArray(obj)) {
    return obj.map(filterObjectSensitive)
  }
  if (obj && typeof obj === 'object') {
    const filtered: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      const lowerKey = key.toLowerCase()
      if (
        lowerKey.includes('key') ||
        lowerKey.includes('token') ||
        lowerKey.includes('secret') ||
        lowerKey.includes('password')
      ) {
        filtered[key] = '***REDACTED***'
      } else {
        filtered[key] = filterObjectSensitive(value)
      }
    }
    return filtered
  }
  return obj
}

const logBuffer = ref<LogEntry[]>([])
const config = ref<LoggerConfig>({
  level: 'INFO',
  enableConsole: true,
  enableFile: false,
  maxEntries: 1000,
})

export function useLogger() {
  const entries = computed(() => logBuffer.value)
  const errorEntries = computed(() => logBuffer.value.filter(e => e.level === 'ERROR'))

  function setConfig(newConfig: Partial<LoggerConfig>) {
    config.value = { ...config.value, ...newConfig }
  }

  function formatTimestamp(): string {
    return new Date().toISOString()
  }

  function addToBuffer(entry: LogEntry) {
    logBuffer.value.push(entry)
    if (logBuffer.value.length > config.value.maxEntries) {
      logBuffer.value.shift()
    }
  }

  function log(
    level: LogLevel,
    module: string,
    message: string,
    data?: Record<string, unknown>,
    error?: Error
  ) {
    if (LOG_LEVELS[level] < LOG_LEVELS[config.value.level]) {
      return
    }

    const filteredMessage = filterSensitiveInfo(message)
    const filteredData = data ? (filterObjectSensitive(data) as Record<string, unknown>) : undefined

    const entry: LogEntry = {
      timestamp: formatTimestamp(),
      level,
      module,
      message: filteredMessage,
      data: filteredData,
      error,
    }

    addToBuffer(entry)

    if (config.value.enableConsole) {
      const prefix = `[${entry.timestamp}] [${level}] [${module}]`
      const consoleMethod =
        level === 'DEBUG'
          ? 'debug'
          : level === 'INFO'
            ? 'info'
            : level === 'WARN'
              ? 'warn'
              : 'error'

      if (error) {
        console[consoleMethod](prefix, filteredMessage, filteredData || '', error)
      } else if (filteredData) {
        console[consoleMethod](prefix, filteredMessage, filteredData)
      } else {
        console[consoleMethod](prefix, filteredMessage)
      }
    }
  }

  function debug(module: string, message: string, data?: Record<string, unknown>) {
    log('DEBUG', module, message, data)
  }

  function info(module: string, message: string, data?: Record<string, unknown>) {
    log('INFO', module, message, data)
  }

  function warn(module: string, message: string, data?: Record<string, unknown>) {
    log('WARN', module, message, data)
  }

  function error(
    module: string,
    message: string,
    err?: Error | unknown,
    data?: Record<string, unknown>
  ) {
    let errorObj: Error | undefined
    let additionalData = data

    if (err instanceof Error) {
      errorObj = err
    } else if (err) {
      if (typeof err === 'object' && err !== null) {
        const errRecord = err as Record<string, unknown>
        const errMessage = String(errRecord.message || errRecord.code || JSON.stringify(err))
        errorObj = new Error(errMessage)
        additionalData = { ...data, errorDetails: err }
      } else {
        errorObj = new Error(String(err))
      }
    }

    log('ERROR', module, message, additionalData, errorObj)
  }

  function clearBuffer() {
    logBuffer.value = []
  }

  function exportLogs(): string {
    return JSON.stringify(logBuffer.value, null, 2)
  }

  function getLogsByLevel(level: LogLevel): LogEntry[] {
    return logBuffer.value.filter(e => e.level === level)
  }

  function getLogsByModule(module: string): LogEntry[] {
    return logBuffer.value.filter(e => e.module === module)
  }

  return {
    entries,
    errorEntries,
    setConfig,
    debug,
    info,
    warn,
    error,
    clearBuffer,
    exportLogs,
    getLogsByLevel,
    getLogsByModule,
  }
}

export const logger = {
  debug(module: string, message: string, data?: Record<string, unknown>) {
    useLogger().debug(module, message, data)
  },
  info(module: string, message: string, data?: Record<string, unknown>) {
    useLogger().info(module, message, data)
  },
  warn(module: string, message: string, data?: Record<string, unknown>) {
    useLogger().warn(module, message, data)
  },
  error(module: string, message: string, err?: Error | unknown, data?: Record<string, unknown>) {
    useLogger().error(module, message, err, data)
  },
}

export type { LogEntry, LoggerConfig }
