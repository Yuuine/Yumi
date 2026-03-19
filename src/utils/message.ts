import type { ChatMessage } from '@/types'

/**
 * 对消息列表进行稳定排序
 *
 * 排序规则（按优先级）：
 * 1. 时间戳升序 - 较早的消息排在前面
 * 2. 角色优先级 - 当时间戳相同时，用户消息排在助手消息前面
 * 3. ID 字典序 - 当时间戳和角色都相同时，按 ID 字典序排序
 *
 * @param msgs - 待排序的消息数组
 * @returns 排序后的新消息数组（不修改原数组）
 *
 * @example
 * ```ts
 * const sorted = sortMessages(messages)
 * ```
 */
export function sortMessages(msgs: ChatMessage[]): ChatMessage[] {
  return [...msgs].sort((a, b) => {
    const timeDiff = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    if (timeDiff !== 0) return timeDiff
    if (a.role !== b.role) {
      return a.role === 'user' ? -1 : 1
    }
    return a.id.localeCompare(b.id)
  })
}
