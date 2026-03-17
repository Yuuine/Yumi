<template>
  <div class="chat-message" :class="message.role">
    <div class="message-avatar">
      <el-avatar :size="36" :src="avatarSrc">
        {{ message.role === 'user' ? 'U' : 'Y' }}
      </el-avatar>
    </div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">{{ roleName }}</span>
        <span class="message-time">{{ formattedTime }}</span>
      </div>
      <div class="message-text" v-html="formattedContent"></div>
      <div v-if="message.emotion && message.role === 'assistant'" class="message-emotion">
        <el-tag size="small" :type="emotionType">
          {{ emotionLabel }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage } from '@/types'
import { useUserStore } from '@/stores'
import { marked } from 'marked'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const props = defineProps<{
  message: ChatMessage
}>()

const userStore = useUserStore()

const avatarSrc = computed(() => {
  return props.message.role === 'user' ? '' : '/yumi-avatar.svg'
})

const roleName = computed(() => {
  return props.message.role === 'user' ? '你' : userStore.profile.roleName
})

const formattedTime = computed(() => {
  return dayjs(props.message.timestamp).fromNow()
})

const formattedContent = computed(() => {
  const content = props.message.content
  try {
    return marked(content) as string
  } catch {
    return content.replace(/\n/g, '<br>')
  }
})

const emotionType = computed(() => {
  if (!props.message.emotion) return 'info'
  const { valence } = props.message.emotion
  if (valence > 0.3) return 'success'
  if (valence < -0.3) return 'warning'
  return 'info'
})

const emotionLabel = computed(() => {
  if (!props.message.emotion) return ''
  const { valence, arousal } = props.message.emotion

  if (valence > 0.5 && arousal > 0.5) return '开心'
  if (valence > 0.5 && arousal <= 0.5) return '平静'
  if (valence < -0.5 && arousal > 0.5) return '担忧'
  if (valence < -0.5 && arousal <= 0.5) return '低落'
  if (arousal > 0.7) return '兴奋'
  return '中性'
})
</script>

<style lang="scss" scoped>
.chat-message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;

  &.user {
    flex-direction: row-reverse;

    .message-content {
      align-items: flex-end;
    }

    .message-text {
      background: var(--el-color-primary-light-9);
      border-radius: 16px 16px 4px 16px;
    }
  }

  &.assistant {
    .message-text {
      background: var(--bg-secondary);
      border-radius: 16px 16px 16px 4px;
    }
  }

  .message-avatar {
    flex-shrink: 0;
  }

  .message-content {
    display: flex;
    flex-direction: column;
    max-width: 70%;

    .message-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;

      .message-role {
        font-size: var(--font-size-xs);
        font-weight: 500;
        color: var(--text-primary);
      }

      .message-time {
        font-size: var(--font-size-xs);
        color: var(--text-secondary);
      }
    }

    .message-text {
      padding: 12px 16px;
      line-height: 1.6;
      word-break: break-word;

      :deep(p) {
        margin: 0 0 8px;
        &:last-child {
          margin-bottom: 0;
        }
      }

      :deep(code) {
        background: rgba(0, 0, 0, 0.05);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.9em;
      }

      :deep(pre) {
        background: rgba(0, 0, 0, 0.05);
        padding: 12px;
        border-radius: 8px;
        overflow-x: auto;

        code {
          background: none;
          padding: 0;
        }
      }
    }

    .message-emotion {
      margin-top: 8px;
    }
  }
}
</style>
