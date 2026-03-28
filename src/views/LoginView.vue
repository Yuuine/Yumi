<template>
  <div class="login-page">
    <StarryBackground :star-count="STAR_COUNT" />

    <div class="glass-card">
      <h1 class="title">{{ activeTab === 'login' ? '欢迎回来' : '创建账号' }}</h1>

      <form @submit.prevent="handleSubmit" class="form">
        <div class="input-wrap">
          <input
            v-model="formData.nickname"
            type="text"
            placeholder="昵称"
            autocomplete="username"
          />
        </div>

        <PasswordInput
          v-model="formData.password"
          placeholder="密码"
          autocomplete="current-password"
        />

        <div class="confirm-input" :class="{ show: activeTab === 'register' }">
          <PasswordInput
            v-model="formData.confirmPassword"
            placeholder="确认密码"
            autocomplete="new-password"
          />
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading">
          <span v-if="!isLoading">{{ activeTab === 'login' ? '登录' : '注册' }}</span>
          <span v-else class="loading-dots">
            <i></i>
            <i></i>
            <i></i>
          </span>
        </button>
      </form>

      <div class="switch">
        {{ activeTab === 'login' ? '还没有账号?' : '已有账号?' }}
        <a href="#" @click.prevent="switchMode(activeTab === 'login' ? 'register' : 'login')">
          {{ activeTab === 'login' ? '注册' : '登录' }}
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores'
import { authApi } from '@/api/auth'
import { logger } from '@/utils/logger'
import { PasswordInput, StarryBackground } from '@/components/common'

const router = useRouter()
const toast = useToast()
const authStore = useAuthStore()

const STAR_COUNT = 200
const NICKNAME_MIN_LENGTH = 2
const NICKNAME_MAX_LENGTH = 20
const PASSWORD_MIN_LENGTH = 6

const activeTab = ref<'login' | 'register'>('login')
const isLoading = ref(false)

const formData = reactive({
  nickname: '',
  password: '',
  confirmPassword: '',
})

function switchMode(mode: 'login' | 'register'): void {
  if (activeTab.value !== mode) {
    activeTab.value = mode
    formData.confirmPassword = ''
  }
}

function validateForm(): boolean {
  if (!formData.nickname.trim()) {
    toast.error('请输入昵称')
    return false
  }
  if (
    formData.nickname.length < NICKNAME_MIN_LENGTH ||
    formData.nickname.length > NICKNAME_MAX_LENGTH
  ) {
    toast.error(`昵称长度需要在 ${NICKNAME_MIN_LENGTH}-${NICKNAME_MAX_LENGTH} 个字符之间`)
    return false
  }
  if (!formData.password) {
    toast.error('请输入密码')
    return false
  }
  if (formData.password.length < PASSWORD_MIN_LENGTH) {
    toast.error(`密码长度至少需要 ${PASSWORD_MIN_LENGTH} 个字符`)
    return false
  }
  if (activeTab.value === 'register' && formData.password !== formData.confirmPassword) {
    toast.error('两次输入的密码不一致')
    return false
  }
  return true
}

async function handleSubmit(): Promise<void> {
  if (!validateForm()) return

  isLoading.value = true
  try {
    let response
    if (activeTab.value === 'register') {
      response = await authApi.register({
        nickname: formData.nickname,
        password: formData.password,
      })
      toast.success('注册成功')
    } else {
      response = await authApi.login({
        nickname: formData.nickname,
        password: formData.password,
      })
      toast.success('登录成功')
    }

    authStore.setTokens(
      response.accessToken,
      response.refreshToken,
      response.userId,
      response.nickname
    )
    await router.push('/')
  } catch (error: unknown) {
    logger.error('LoginView', 'Authentication failed', error as Record<string, unknown>)
    const err = error as { message?: string; detail?: { message?: string } }
    toast.error(
      err.message || err.detail?.message || (activeTab.value === 'login' ? '登录失败' : '注册失败')
    )
  } finally {
    isLoading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.glass-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 380px;
  padding: 48px 40px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.title {
  font-size: 28px;
  font-weight: 600;
  color: white;
  text-align: center;
  margin: 0 0 32px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-wrap {
  position: relative;

  input {
    width: 100%;
    padding: 14px 16px;
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    font-size: 15px;
    color: white;
    outline: none;
    transition: all 0.2s ease;
    box-sizing: border-box;

    &::placeholder {
      color: rgba(255, 255, 255, 0.6);
    }

    &:focus {
      background: rgba(255, 255, 255, 0.25);
      border-color: rgba(255, 255, 255, 0.5);
    }
  }
}

.confirm-input {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transition: all 0.3s ease;

  &.show {
    max-height: 60px;
    opacity: 1;
  }
}

.submit-btn {
  width: 100%;
  padding: 14px;
  margin-top: 8px;
  background: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #e73c7e;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

.loading-dots {
  display: flex;
  justify-content: center;
  gap: 4px;

  i {
    width: 6px;
    height: 6px;
    background: #e73c7e;
    border-radius: 50%;
    animation: bounce 0.5s ease-in-out infinite;

    &:nth-child(2) {
      animation-delay: 0.1s;
    }
    &:nth-child(3) {
      animation-delay: 0.2s;
    }
  }
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.switch {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);

  a {
    color: white;
    font-weight: 600;
    text-decoration: none;
    margin-left: 4px;

    &:hover {
      text-decoration: underline;
    }
  }
}

@media (max-width: 480px) {
  .glass-card {
    margin: 20px;
    padding: 36px 28px;
  }

  .title {
    font-size: 24px;
  }
}
</style>
