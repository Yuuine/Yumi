# 聊天区滚动行为排查说明

## 需求回顾

1. **非流式发送**：新消息出现后应**平滑**滚到底部，保证新消息可见。
2. **用户上滑读历史**：新到达的消息**不应**强制滚动，避免打断阅读。

## 根因分析（为何「完全未实现」）

### 1. `endStickyFollow()` 调用时机错误（主因）

实现上，`ChatView.handleSend` 在 `try/finally` 中于 `await chatStore.sendMessage(...)` **返回后立即**调用 `messageListRef.endStickyFollow()`。

执行顺序大致为：

1. `sendMessage` 在服务端返回后向 `messages` 追加助手消息；
2. Vue 将 `MessageList` 中对 `props.messages` 的 `watch` 调度到微任务队列；
3. `sendMessage` 返回，`handleSend` 进入 **`finally`，同步执行 `endStickyFollow()`**，将 `stickyFollowActive` 置为 `false`；
4. 随后才执行 `MessageList` 的 `watch` 回调，其中 `scheduleFollowScroll` → `runFollowScrollFrame` 在 `nextTick` + `requestAnimationFrame` 里检查 `shouldAutoScroll()`；
5. 此时 **`stickyFollowActive` 已为 false**；若平滑滚动尚未把视口带到底部，`isAtBottom` 也可能仍为 false；
6. `shouldAutoScroll()` 返回 false → **不滚动**，表现为「发送后根本不跟到底部」。

因此问题不是「没有写平滑滚动」，而是 **粘性状态在滚动逻辑执行前被清掉**，与设计意图相反。

### 2. 设计层面评估

- **粘性会话（`beginStickyFollow` / `endStickyFollow`）+ `shouldAutoScroll = sticky || isAtBottom`** 的设计可行：用户离开底部会 `clearStickyIfUserAway()`，读历史时不会跟滚。
- **缺陷**在于 **结束粘性的时机必须与 Vue 刷新、`MessageList` 内调度对齐**，不能放在与 `await sendMessage` 同一同步段落的 `finally` 末尾。

### 3. 其他次要问题

- **切换会话且两条会话消息条数相同**时，`MessageList` 曾走「同长度、非最后一条内容更新」分支，可能不触发「首屏滚到底」。已通过监听 `currentConversationId` 重置 `isInitialLoad` 缓解（**仅在 `prev !== undefined` 时重置**，避免首次挂载把 `isInitialLoad` 再次置 true，打乱后续「新消息」分支）。

## 已做改进

| 位置 | 改动 |
|------|------|
| `ChatView.vue` | `finally` 中在 `nextTick` + **双 `requestAnimationFrame`** 之后再调用 `endStickyFollow()`，确保滚动调度先排队执行。 |
| `MessageList.vue` | `watch(chatStore.currentConversationId)`：会话 id 变化时 `isInitialLoad = true`，切换会话后仍能滚到底。 |

## 行为与预期对应关系

| 场景 | 机制 |
|------|------|
| 发送后需跟到底 | `beginStickyFollow()` 为 true → `shouldAutoScroll` 为 true → `scheduleFollowScroll` 使用 `scrollToBottomSmooth`（非流式）。 |
| 用户上滑读历史 | `handleScroll` 中 `clearStickyIfUserAway()`，离开底部超过阈值则 `stickyFollowActive = false`；新消息到达时 `shouldAutoScroll` 为 false → **不滚动**；「回到底部」按钮可见。 |
| 流式 | 仍用节流 + 瞬时对齐；`endStickyFollow` 延迟同样适用。 |

## 后续优化（已实现）

- **`ResizeObserver`**：监听 `messages-wrapper` 尺寸变化，在 **`stickyFollowActive` 或当前已在底部**（`dist < BOTTOM_THRESHOLD`）时用 `requestAnimationFrame` 合并回调并 **瞬时** `scrollToBottomInstant`，避免 Markdown/图片撑高后底部留白；读历史时不在底部则不补滚。
- **`completeStickyFollowSession()`**：由 `MessageList` 封装 `nextTick` + 双 `rAF` 后再 `endStickyFollow`，`ChatView` 的 `finally` 仅调用该异步方法，避免父组件重复样板代码。
