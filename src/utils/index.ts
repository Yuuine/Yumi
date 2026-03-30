/**
 * 通用工具函数模块
 */

export {
  formatDateTime,
  copyToClipboard,
  camelToSnake,
  snakeToCamel,
  keysToSnake,
  keysToCamel,
} from './common'
export {
  TypewriterBuffer,
  createTypewriterBuffer,
  type TypewriterBufferConfig,
} from './typewriter-buffer'
export {
  measureTextHeight,
  clearMeasurementCache,
  createTextMeasurer,
  type TextMeasurementConfig,
} from './text-measurement'
export { convertObjectKeys } from './transform'
export { dayjs, formatRelativeTime } from './datetime'
export { renderMarkdown } from './markdown'
export {
  generateAccountId,
  generateCharacterId,
  generateConversationId,
  generateMessageId,
  generateSecretId,
  buildChecksumSource,
  sha256Hex,
  isEncryptedData,
  isAccountExportData,
  countMessages,
  decryptModelSecrets,
  remapImportIds,
} from './account-helpers'
