<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-container">
          <svg class="logo-icon" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="64" height="64" rx="16" fill="#6366f1"/>
            <path d="M20 22C20 19.7909 21.7909 18 24 18H40C42.2091 18 44 19.7909 44 22V42C44 44.2091 42.2091 46 40 46H24C21.7909 46 20 44.2091 20 42V22Z" fill="white"/>
            <circle cx="32" cy="40" r="3" fill="#6366f1"/>
          </svg>
        </div>
        <h1 class="app-title">Yumi</h1>
        <p class="app-subtitle">你的 AI 虚拟伴侣</p>
      </div>

      <div class="mode-switch">
        <button
          class="mode-button"
          :class="{ active: activeTab === 'login' }"
          @click="switchMode('login')"
          :aria-pressed="activeTab === 'login'"
        >
          <span class="mode-text">登录</span>
        </button>
        <button
          class="mode-button"
          :class="{ active: activeTab === 'register' }"
          @click="switchMode('register')"
          :aria-pressed="activeTab === 'register'"
        >
          <span class="mode-text">注册</span>
        </button>
        <div class="mode-indicator" :style="indicatorStyle"></div>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form" novalidate>
        <div class="form-field">
          <label for="nickname" class="field-label">
            昵称
            <span class="required">*</span>
          </label>
          <div class="input-wrapper">
            <input
              id="nickname"
              v-model="formData.nickname"
              type="text"
              class="field-input"
              :placeholder="activeTab === 'register' ? '请输入 2-20 个字符' : '请输入昵称'"
              autocomplete="username"
              required
              :minlength="2"
              :maxlength="20"
            />
          </div>
        </div>

        <div class="form-field">
          <label for="password" class="field-label">
            密码
            <span class="required">*</span>
          </label>
          <div class="input-wrapper">
            <input
              id="password"
              v-model="formData.password"
              :type="showPassword ? 'text' : 'password'"
              class="field-input"
              placeholder="请输入至少 6 个字符"
              autocomplete="current-password"
              required
              :minlength="6"
              :maxlength="128"
            />
            <button
              type="button"
              class="password-toggle"
              @click="showPassword = !showPassword"
              tabindex="-1"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
            >
              <svg v-if="!showPassword" class="toggle-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M1 10s3-6 9-6 9 6 9 6-3 6-9 6-9-6-9-6z"/>
                <circle cx="10" cy="10" r="2.5"/>
              </svg>
              <svg v-else class="toggle-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M15 15a6 6 0 01-10 0M5 5a6 6 0 0110 0"/>
                <line x1="1" y1="1" x2="19" y2="19"/>
              </svg>
            </button>
          </div>
        </div>

        <Transition name="confirm-password">
          <div v-if="activeTab === 'register'" class="form-field" key="confirm-password">
            <label for="confirmPassword" class="field-label">
              确认密码
              <span class="required">*</span>
            </label>
            <div class="input-wrapper">
              <input
                id="confirmPassword"
                v-model="formData.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                class="field-input"
                placeholder="请再次输入密码"
                autocomplete="new-password"
                required
                :minlength="6"
              />
              <button
                type="button"
                class="password-toggle"
                @click="showConfirmPassword = !showConfirmPassword"
                tabindex="-1"
                :aria-label="showConfirmPassword ? '隐藏密码' : '显示密码'"
              >
                <svg v-if="!showConfirmPassword" class="toggle-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M1 10s3-6 9-6 9 6 9 6-3 6-9 6-9-6-9-6z"/>
                  <circle cx="10" cy="10" r="2.5"/>
                </svg>
                <svg v-else class="toggle-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M15 15a6 6 0 01-10 0M5 5a6 6 0 0110 0"/>
                  <line x1="1" y1="1" x2="19" y2="19"/>
                </svg>
              </button>
            </div>
          </div>
        </Transition>

        <button
          type="submit"
          class="submit-button"
          :disabled="isLoading"
          :aria-busy="isLoading"
        >
          <span v-if="isLoading" class="loading-spinner" aria-hidden="true"></span>
          <span v-else>{{ activeTab === 'login' ? '登录' : '注册' }}</span>
        </button>
      </form>

      <div class="login-footer">
        <div class="divider">
          <span class="divider-line"></span>
          <span class="divider-text">或</span>
          <span class="divider-line"></span>
        </div>
        <p class="footer-text">
          {{ activeTab === 'login' ? '还没有账号？' : '已有账号？' }}
          <button
            type="button"
            class="switch-button"
            @click="switchMode(activeTab === 'login' ? 'register' : 'login')"
          >
            {{ activeTab === 'login' ? '立即注册' : '立即登录' }}
          </button>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { authApi } from '@/api/auth'
import { logger } from '@/utils/logger'

const router = useRouter()
const toast = useToast()

const activeTab = ref<'login' | 'register'>('login')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const isLoading = ref(false)

const formData = reactive({
  nickname: '',
  password: '',
  confirmPassword: ''
})

const indicatorStyle = computed(() => {
  const left = activeTab.value === 'login' ? '4px' : 'calc(50% + 2px)'
  return {
    left,
    width: 'calc(50% - 6px)'
  }
})

function switchMode(mode: 'login' | 'register'): void {
  if (activeTab.value !== mode) {
    activeTab.value = mode
    formData.confirmPassword = ''
    showConfirmPassword.value = false
  }
}

function validateForm(): boolean {
  if (!formData.nickname.trim()) {
    toast.error('请输入昵称')
    return false
  }

  if (formData.nickname.length < 2 || formData.nickname.length > 20) {
    toast.error('昵称长度需要在 2-20 个字符之间')
    return false
  }

  if (!formData.password) {
    toast.error('请输入密码')
    return false
  }

  if (formData.password.length < 6) {
    toast.error('密码长度至少需要 6 个字符')
    return false
  }

  if (activeTab.value === 'register' && formData.password !== formData.confirmPassword) {
    toast.error('两次输入的密码不一致')
    return false
  }

  return true
}

async function handleSubmit(): Promise<void> {
  if (!validateForm()) {
    return
  }

  isLoading.value = true

  try {
    let response

    if (activeTab.value === 'login') {
      response = await authApi.login({
        nickname: formData.nickname,
        password: formData.password
      })
    } else {
      response = await authApi.register({
        nickname: formData.nickname,
        password: formData.password
      })
    }

    localStorage.setItem('yumi_access_token', response.accessToken)
    localStorage.setItem('yumi_refresh_token', response.refreshToken)
    localStorage.setItem('yumi_user_id', response.userId)

    toast.success(activeTab.value === 'login' ? '登录成功' : '注册成功')
    logger.info('LoginView', 'Authentication successful', { userId: response.userId })

    await router.push('/')
  } catch (error: unknown) {
    logger.error('LoginView', 'Authentication failed', error as Record<string, unknown>)
    
    if (error instanceof Error) {
      toast.error(error.message || (activeTab.value === 'login' ? '登录失败，请检查昵称和密码' : '注册失败，请稍后重试'))
    } else {
      toast.error(activeTab.value === 'login' ? '登录失败，请检查昵称和密码' : '注册失败，请稍后重试')
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style lang="scss">
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
  background: #ffffff;
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 48px 40px;
  background: white;
  animation: cardEnter 0.5s ease-out;
}

@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.logo-icon {
  width: 64px;
  height: 64px;
  animation: logoFloat 3s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.app-title {
  font-size: 32px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 6px;
  letter-spacing: -0.5px;
}

.app-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  font-weight: 400;
}

.mode-switch {
  display: flex;
  gap: 0;
  background: #f3f4f6;
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 32px;
  position: relative;
}

.mode-button {
  flex: 1;
  padding: 10px 16px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  position: relative;
  z-index: 1;
  transition: color 0.2s ease;

  &:hover:not(.active) {
    color: #374151;
  }

  &.active {
    color: #1f2937;
  }
}

.mode-indicator {
  position: absolute;
  top: 4px;
  height: calc(100% - 8px);
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: none;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-field {
  position: relative;
  min-height: 72px;
}

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.required {
  color: #ef4444;
  font-weight: 600;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.field-input {
  width: 100%;
  padding: 12px 14px;
  padding-right: 44px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  color: #1f2937;
  background: white;
  transition: all 0.2s ease;
  outline: none;

  &::placeholder {
    color: #9ca3af;
  }

  &:focus {
    border-color: #6366f1;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
  }

  &:hover:not(:focus) {
    border-color: #d1d5db;
  }
}

.password-toggle {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  padding: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;

  &:hover {
    opacity: 1;
  }
}

.toggle-icon {
  width: 18px;
  height: 18px;
  color: #6b7280;
  flex-shrink: 0;
}

.submit-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 20px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: white;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 8px;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-footer {
  margin-top: 32px;
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: #e5e7eb;
}

.divider-text {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}

.footer-text {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  text-align: center;
}

.switch-button {
  border: none;
  background: transparent;
  color: #6366f1;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  margin-left: 4px;
  transition: color 0.2s ease;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 0;
    height: 2px;
    background: #6366f1;
    transition: width 0.2s ease;
  }

  &:hover {
    color: #4f46e5;
  }

  &:hover::after {
    width: 100%;
  }
}

.confirm-password-enter-active,
.confirm-password-leave-active {
  overflow: hidden;
}

.confirm-password-enter-active {
  transition: opacity 0.35s ease-out, transform 0.35s ease-out, max-height 0.4s ease-out, margin-bottom 0.4s ease-out;
}

.confirm-password-leave-active {
  transition: opacity 0.25s ease-in, transform 0.25s ease-in, max-height 0.3s ease-in, margin-bottom 0.3s ease-in;
}

.confirm-password-enter-from {
  opacity: 0;
  transform: translateY(-12px);
  max-height: 0;
  margin-bottom: -20px;
}

.confirm-password-leave-to {
  opacity: 0;
  transform: translateY(-6px);
  max-height: 0;
  margin-bottom: -20px;
}
</style>
