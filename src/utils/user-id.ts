/**
 * 用户标识工具
 * 用于生成和持久化匿名用户ID
 */

const USER_ID_KEY = 'yumi_user_id'

/**
 * 获取或创建用户ID
 * 如果 localStorage 中已存在用户ID，则返回
 * 否则生成新的匿名用户ID并存储
 */
export function getOrCreateUserId(): string {
  let userId = localStorage.getItem(USER_ID_KEY)
  
  if (!userId) {
    userId = `anonymous-${crypto.randomUUID()}`
    localStorage.setItem(USER_ID_KEY, userId)
  }
  
  return userId
}
