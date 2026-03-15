<template>
  <div class="settings-view">
    <div class="sidebar">
      <div class="sidebar-header">
        <el-avatar :size="48">Y</el-avatar>
        <h2>设置</h2>
      </div>
      <el-menu :default-active="activeMenu" router>
        <el-menu-item index="/">
          <el-icon><ChatDotRound /></el-icon>
          <span>返回对话</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <span>角色设定</span>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="settings-main">
      <div class="settings-header">
        <h3>应用设置</h3>
      </div>

      <el-form
        ref="formRef"
        :model="settingsStore.settings"
        label-width="140px"
        class="settings-form"
        @submit.prevent
      >
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>API 配置</span>
            </div>
          </template>

          <el-form-item label="API 端点">
            <el-input v-model="formData.apiEndpoint" placeholder="http://127.0.0.1:11434/v1" />
            <div class="form-tip">支持 OpenAI 兼容 API，如 Ollama、vLLM 等</div>
          </el-form-item>

          <el-form-item label="API Key">
            <el-input
              v-model="formData.apiKey"
              type="password"
              placeholder="可选，本地部署无需填写"
              show-password
            />
          </el-form-item>

          <el-form-item label="模型名称">
            <el-input v-model="formData.modelName" placeholder="llama3.1:8b" />
          </el-form-item>
        </el-card>

        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>生成参数</span>
            </div>
          </template>

          <el-form-item label="温度 (Temperature)">
            <el-slider v-model="formData.temperature" :min="0" :max="2" :step="0.05" show-input />
            <div class="form-tip">较高的值使输出更随机，较低的值更确定</div>
          </el-form-item>

          <el-form-item label="最大 Token 数">
            <el-input-number v-model="formData.maxTokens" :min="256" :max="8192" :step="256" />
          </el-form-item>
        </el-card>

        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>功能开关</span>
            </div>
          </template>

          <el-form-item label="长期记忆">
            <el-switch v-model="formData.memoryEnabled" />
            <div class="form-tip">启用后 AI 会记住之前的对话内容</div>
          </el-form-item>

          <el-form-item label="情感检测">
            <el-switch v-model="formData.emotionDetection" />
            <div class="form-tip">分析对话情感，提供更贴心的回应</div>
          </el-form-item>
        </el-card>

        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>外观设置</span>
            </div>
          </template>

          <el-form-item label="主题">
            <el-radio-group v-model="formData.theme" @change="handleThemeChange">
              <el-radio value="light">浅色</el-radio>
              <el-radio value="dark">深色</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="语言">
            <el-select v-model="formData.language">
              <el-option label="简体中文" value="zh-CN" />
              <el-option label="English" value="en-US" />
            </el-select>
          </el-form-item>
        </el-card>

        <div class="form-actions">
          <el-button @click="resetForm">重置</el-button>
          <el-button type="primary" @click="saveSettings" :loading="saving">保存设置</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, User } from '@element-plus/icons-vue'
import { useSettingsStore } from '@/stores'
import type { AppSettings } from '@/types'

const route = useRoute()
const settingsStore = useSettingsStore()

const activeMenu = ref(route.path)
const saving = ref(false)
const formRef = ref()

const formData = reactive<AppSettings>({
  apiEndpoint: '',
  apiKey: '',
  modelName: '',
  maxTokens: 4096,
  temperature: 0.85,
  memoryEnabled: true,
  emotionDetection: true,
  theme: 'light',
  language: 'zh-CN',
})

watch(
  () => route.path,
  path => {
    activeMenu.value = path
  }
)

watch(
  () => settingsStore.settings,
  settings => {
    Object.assign(formData, settings)
  },
  { immediate: true, deep: true }
)

onMounted(async () => {
  await settingsStore.loadSettings()
  Object.assign(formData, settingsStore.settings)
})

function handleThemeChange(theme: string | number | boolean | undefined) {
  if (theme === 'light' || theme === 'dark') {
    settingsStore.setTheme(theme)
  }
}

async function saveSettings() {
  saving.value = true
  try {
    await settingsStore.updateSettings({ ...formData })
    ElMessage.success('设置已保存')
  } catch (_error) {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

function resetForm() {
  Object.assign(formData, settingsStore.settings)
}
</script>

<style lang="scss" scoped>
.settings-view {
  display: flex;
  height: 100vh;
  background: var(--bg-primary);
}

.sidebar {
  width: 240px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color, #e4e7ed);
  padding: 20px;

  .sidebar-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 18px;
      color: var(--text-primary);
    }
  }

  :deep(.el-menu) {
    border: none;
    background: transparent;
  }

  :deep(.el-menu-item) {
    border-radius: 8px;
    margin: 4px 0;
  }
}

.settings-main {
  flex: 1;
  padding: 24px;
  overflow-y: auto;

  .settings-header {
    margin-bottom: 24px;

    h3 {
      margin: 0;
      font-size: 20px;
      color: var(--text-primary);
    }
  }

  .settings-form {
    max-width: 600px;

    .settings-card {
      margin-bottom: 20px;

      .card-header {
        font-weight: 500;
      }
    }

    .form-tip {
      font-size: 12px;
      color: var(--text-secondary);
      margin-top: 4px;
    }
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 24px;
  }
}
</style>
