import type { ChatMessage } from '@/types'

/**
 * 解析消息时间戳为毫秒数（无效则返回 0）
 */
function parseMessageTimeMs(m: ChatMessage): number {
  const t = Date.parse(m.timestamp)
  return Number.isNaN(t) ? 0 : t
}

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
 */
export function sortMessages(msgs: ChatMessage[]): ChatMessage[] {
  return [...msgs].sort((a, b) => {
    const timeDiff = parseMessageTimeMs(a) - parseMessageTimeMs(b)
    if (timeDiff !== 0) return timeDiff
    if (a.role !== b.role) {
      return a.role === 'user' ? -1 : 1
    }
    return a.id.localeCompare(b.id)
  })
}

/**
 * 按 id 去重，后出现的覆盖先出现的（通常保留较新合并结果）
 */
export function dedupeMessagesById(msgs: ChatMessage[]): ChatMessage[] {
  const map = new Map<string, ChatMessage>()
  for (const m of msgs) {
    if (m?.id) {
      map.set(m.id, m)
    }
  }
  return sortMessages([...map.values()])
}

/**
 * 合并两段消息历史（如加载更早一页时与当前列表合并），去重后按时间排序
 */
export function mergeMessageHistory(
  olderWindow: ChatMessage[],
  newerWindow: ChatMessage[]
): ChatMessage[] {
  return dedupeMessagesById([...olderWindow, ...newerWindow])
}
