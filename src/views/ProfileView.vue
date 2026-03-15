<template>
  <div class="profile-view">
    <div class="sidebar">
      <div class="sidebar-header">
        <el-avatar :size="48">Y</el-avatar>
        <h2>角色设定</h2>
      </div>
      <el-menu :default-active="activeMenu" router>
        <el-menu-item index="/">
          <el-icon><ChatDotRound /></el-icon>
          <span>返回对话</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>应用设置</span>
        </el-menu-item>
      </el-menu>
    </div>

    <div class="profile-main">
      <div class="profile-header">
        <h3>个性化设置</h3>
        <p>定制你的专属 AI 伴侣</p>
      </div>

      <el-form ref="formRef" :model="userStore.profile" label-width="120px" class="profile-form">
        <el-card class="profile-card">
          <template #header>
            <div class="card-header">
              <span>基本信息</span>
            </div>
          </template>

          <el-form-item label="角色名称">
            <el-input v-model="profileData.roleName" placeholder="给 AI 起个名字" />
          </el-form-item>
        </el-card>

        <el-card class="profile-card">
          <template #header>
            <div class="card-header">
              <span>性格特质 (大五人格)</span>
              <el-tooltip content="调整这些参数会影响 AI 的回复风格">
                <el-icon><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>

          <el-form-item label="开放性">
            <el-slider
              v-model="profileData.bigFive.openness"
              :min="0"
              :max="1"
              :step="0.05"
              :format-tooltip="(val: number) => formatTrait(val, 'openness')"
            />
            <div class="trait-desc">
              {{ getTraitDescription('openness', profileData.bigFive.openness) }}
            </div>
          </el-form-item>

          <el-form-item label="尽责性">
            <el-slider
              v-model="profileData.bigFive.conscientiousness"
              :min="0"
              :max="1"
              :step="0.05"
              :format-tooltip="(val: number) => formatTrait(val, 'conscientiousness')"
            />
            <div class="trait-desc">
              {{ getTraitDescription('conscientiousness', profileData.bigFive.conscientiousness) }}
            </div>
          </el-form-item>

          <el-form-item label="外向性">
            <el-slider
              v-model="profileData.bigFive.extraversion"
              :min="0"
              :max="1"
              :step="0.05"
              :format-tooltip="(val: number) => formatTrait(val, 'extraversion')"
            />
            <div class="trait-desc">
              {{ getTraitDescription('extraversion', profileData.bigFive.extraversion) }}
            </div>
          </el-form-item>

          <el-form-item label="亲和性">
            <el-slider
              v-model="profileData.bigFive.agreeableness"
              :min="0"
              :max="1"
              :step="0.05"
              :format-tooltip="(val: number) => formatTrait(val, 'agreeableness')"
            />
            <div class="trait-desc">
              {{ getTraitDescription('agreeableness', profileData.bigFive.agreeableness) }}
            </div>
          </el-form-item>

          <el-form-item label="神经质">
            <el-slider
              v-model="profileData.bigFive.neuroticism"
              :min="0"
              :max="1"
              :step="0.05"
              :format-tooltip="(val: number) => formatTrait(val, 'neuroticism')"
            />
            <div class="trait-desc">
              {{ getTraitDescription('neuroticism', profileData.bigFive.neuroticism) }}
            </div>
          </el-form-item>
        </el-card>

        <el-card class="profile-card">
          <template #header>
            <div class="card-header">
              <span>对话偏好</span>
            </div>
          </template>

          <el-form-item label="沟通风格">
            <el-select v-model="profileData.preferences.communicationStyle">
              <el-option label="温暖亲切" value="warm" />
              <el-option label="专业理性" value="professional" />
              <el-option label="活泼幽默" value="playful" />
              <el-option label="温柔细腻" value="gentle" />
            </el-select>
          </el-form-item>

          <el-form-item label="感兴趣话题">
            <el-select
              v-model="profileData.preferences.topicsOfInterest"
              multiple
              placeholder="选择感兴趣的话题"
            >
              <el-option label="生活日常" value="生活" />
              <el-option label="工作职场" value="工作" />
              <el-option label="情感心理" value="情感" />
              <el-option label="科技数码" value="科技" />
              <el-option label="文学艺术" value="艺术" />
              <el-option label="健康运动" value="健康" />
              <el-option label="旅行美食" value="旅行" />
              <el-option label="游戏动漫" value="游戏" />
            </el-select>
          </el-form-item>

          <el-form-item label="情感支持">
            <el-radio-group v-model="profileData.preferences.emotionalSupportLevel">
              <el-radio value="high">高度共情</el-radio>
              <el-radio value="medium">适度支持</el-radio>
              <el-radio value="low">理性分析</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="回复长度">
            <el-radio-group v-model="profileData.preferences.responseLength">
              <el-radio value="short">简洁</el-radio>
              <el-radio value="medium">适中</el-radio>
              <el-radio value="long">详细</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-card>

        <div class="form-actions">
          <el-button @click="resetForm">重置</el-button>
          <el-button type="primary" @click="saveProfile" :loading="saving">保存设置</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Setting, QuestionFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores'
import type { BigFiveTraits, UserPreferences } from '@/types'

const route = useRoute()
const userStore = useUserStore()

const activeMenu = ref(route.path)
const saving = ref(false)

const profileData = reactive({
  roleName: '',
  bigFive: {
    openness: 0.75,
    conscientiousness: 0.7,
    extraversion: 0.65,
    agreeableness: 0.8,
    neuroticism: 0.35,
  },
  preferences: {
    communicationStyle: 'warm',
    topicsOfInterest: [] as string[],
    emotionalSupportLevel: 'high',
    responseLength: 'medium',
  },
})

watch(
  () => route.path,
  path => {
    activeMenu.value = path
  }
)

watch(
  () => userStore.profile,
  profile => {
    profileData.roleName = profile.roleName
    Object.assign(profileData.bigFive, profile.bigFive)
    Object.assign(profileData.preferences, profile.preferences)
  },
  { immediate: true, deep: true }
)

onMounted(async () => {
  await userStore.loadProfile()
  Object.assign(profileData, userStore.profile)
})

const traitDescriptions: Record<string, { low: string; high: string }> = {
  openness: {
    low: '务实、传统，偏好熟悉的事物',
    high: '好奇、创意丰富，喜欢探索新事物',
  },
  conscientiousness: {
    low: '随性、灵活，享受当下',
    high: '有条理、自律，注重计划',
  },
  extraversion: {
    low: '内向、安静，喜欢独处',
    high: '外向、活跃，喜欢社交',
  },
  agreeableness: {
    low: '直接、独立，有主见',
    high: '友善、体贴，善解人意',
  },
  neuroticism: {
    low: '情绪稳定、从容',
    high: '敏感、细腻，情感丰富',
  },
}

function formatTrait(value: number, trait: string): string {
  const labels: Record<string, { low: string; high: string }> = {
    openness: { low: '传统', high: '开放' },
    conscientiousness: { low: '随性', high: '尽责' },
    extraversion: { low: '内向', high: '外向' },
    agreeableness: { low: '独立', high: '亲和' },
    neuroticism: { low: '稳定', high: '敏感' },
  }

  if (value < 0.3) return labels[trait].low
  if (value > 0.7) return labels[trait].high
  return '适中'
}

function getTraitDescription(trait: string, value: number): string {
  const desc = traitDescriptions[trait]
  if (value < 0.3) return desc.low
  if (value > 0.7) return desc.high
  return '介于两者之间'
}

async function saveProfile() {
  saving.value = true
  try {
    await userStore.updateProfile({
      ...userStore.profile,
      roleName: profileData.roleName,
      bigFive: { ...profileData.bigFive } as BigFiveTraits,
      preferences: { ...profileData.preferences } as UserPreferences,
    })
    ElMessage.success('角色设定已保存')
  } catch (_error) {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

function resetForm() {
  Object.assign(profileData, userStore.profile)
}
</script>

<style lang="scss" scoped>
.profile-view {
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

.profile-main {
  flex: 1;
  padding: 24px;
  overflow-y: auto;

  .profile-header {
    margin-bottom: 24px;

    h3 {
      margin: 0 0 4px;
      font-size: 20px;
      color: var(--text-primary);
    }

    p {
      margin: 0;
      color: var(--text-secondary);
    }
  }

  .profile-form {
    max-width: 600px;

    .profile-card {
      margin-bottom: 20px;

      .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 500;
      }
    }

    .trait-desc {
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
