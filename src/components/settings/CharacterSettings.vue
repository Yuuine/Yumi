<template>
  <div class="character-settings">
    <div v-if="draft" class="config-root">
      <nav class="section-nav" aria-label="表单章节">
        <button
          v-for="nav in sectionNav"
          :key="nav.id"
          type="button"
          class="section-nav-item"
          :class="{ active: activeSection === nav.id }"
          @click="scrollToSection(nav.id)"
        >
          <span class="section-nav-text">{{ nav.label }}</span>
        </button>
      </nav>

      <div ref="scrollEl" class="config-scroll">
        <section id="char-section-basic" class="config-section">
          <header class="section-header">
            <h3 class="section-heading">基础档案</h3>
            <p class="section-desc">定义角色的基本身份与外貌信息</p>
            <p class="section-required-note">
              <span class="required-mark">*</span>
              为必填项
            </p>
          </header>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">
                正式名
                <span class="required-mark">*</span>
              </label>
              <input v-model="draft.name" class="form-input" type="text" maxlength="30" />
            </div>
            <div class="form-group full-width">
              <label class="form-label">昵称</label>
              <TagsInput v-model="draft.nickname" separator="、" placeholder="输入后按回车添加" />
            </div>
            <div class="form-group full-width">
              <label class="form-label">
                角色概述
                <span class="required-mark">*</span>
              </label>
              <AutoResizeTextarea
                v-model="draft.roleOverview"
                :min-height="64"
                :max-height="200"
                placeholder="描述这个角色是谁..."
              />
            </div>
            <div class="form-group">
              <label class="form-label">种族/形式</label>
              <input v-model="draft.appearance.race" class="form-input" type="text" />
            </div>
            <div class="form-group">
              <label class="form-label">性别</label>
              <div class="gender-selector">
                <button
                  v-for="option in genderOptions"
                  :key="option.value"
                  type="button"
                  class="gender-option"
                  :class="{ active: draft.appearance.gender === option.value }"
                  @click="draft.appearance.gender = option.value"
                >
                  <span class="gender-label">{{ option.label }}</span>
                </button>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">外表年龄</label>
              <input v-model="draft.appearance.visualAge" class="form-input" type="text" />
            </div>
            <div class="form-group">
              <label class="form-label">实际年龄</label>
              <input v-model="draft.appearance.actualAge" class="form-input" type="text" />
            </div>
            <div class="form-group full-width">
              <label class="form-label">所在地</label>
              <input v-model="draft.appearance.location" class="form-input" type="text" />
            </div>
            <div class="form-group full-width">
              <label class="form-label">外貌描述</label>
              <AutoResizeTextarea
                v-model="draft.appearance.description"
                :min-height="64"
                :max-height="180"
                placeholder="描述角色的外貌特征..."
              />
            </div>
          </div>
        </section>

        <section id="char-section-personality" class="config-section">
          <header class="section-header">
            <h3 class="section-heading">性格与态度</h3>
            <p class="section-desc">性格特点与对用户的态度</p>
          </header>
          <div class="form-group">
            <label class="form-label">核心性格</label>
            <TagsInput
              v-model="draft.personality.core"
              separator="、"
              placeholder="输入后按回车添加"
            />
          </div>
          <div class="form-group">
            <label class="form-label">自我认知</label>
            <TagsInput
              v-model="draft.personality.selfPerception"
              separator="、"
              placeholder="输入后按回车添加"
            />
          </div>
          <div class="form-group">
            <label class="form-label">对用户态度</label>
            <TagsInput
              v-model="draft.personality.attitudeToUser"
              separator="、"
              placeholder="输入后按回车添加"
            />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">喜好</label>
              <TagsInput
                v-model="draft.personality.likes"
                separator="、"
                placeholder="输入后按回车添加"
              />
            </div>
            <div class="form-group">
              <label class="form-label">厌恶/雷点</label>
              <TagsInput
                v-model="draft.personality.dislikes"
                separator="、"
                placeholder="输入后按回车添加"
              />
            </div>
          </div>
        </section>

        <section id="char-section-language" class="config-section">
          <header class="section-header">
            <h3 class="section-heading">语言风格</h3>
            <p class="section-desc">语气、用词与表达习惯</p>
          </header>
          <div class="form-group">
            <label class="form-label">语气基调</label>
            <TagsInput
              v-model="draft.communication.toneBase"
              separator="、"
              placeholder="输入后按回车添加"
            />
          </div>
          <div class="form-group">
            <label class="form-label">用词习惯</label>
            <AutoResizeTextarea
              v-model="draft.communication.wordHabits"
              :min-height="56"
              :max-height="140"
              placeholder="描述角色的用词习惯..."
            />
          </div>
          <div class="form-group">
            <label class="form-label">情感表达规则</label>
            <div class="emotion-rules-container">
              <label class="emotion-rule-item">
                <input type="checkbox" v-model="emotionRules.emoji" @change="updateEmotionRules" />
                <span class="emotion-rule-label">表情符号</span>
              </label>
              <label class="emotion-rule-item">
                <input
                  type="checkbox"
                  v-model="emotionRules.modalParticles"
                  @change="updateEmotionRules"
                />
                <span class="emotion-rule-label">语气词</span>
              </label>
              <label class="emotion-rule-item">
                <input
                  type="checkbox"
                  v-model="emotionRules.punctuationEmotion"
                  @change="updateEmotionRules"
                />
                <span class="emotion-rule-label">标点符号表达情绪</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">对话长度偏好</label>
            <AutoResizeTextarea
              v-model="draft.communication.lengthPref"
              :min-height="56"
              :max-height="140"
              placeholder="描述角色偏好的对话长度..."
            />
          </div>
        </section>

        <section id="char-section-scenarios" class="config-section">
          <header class="section-header">
            <h3 class="section-heading">特殊情境反应</h3>
            <p class="section-desc">特定场景下的行为与回复逻辑</p>
          </header>
          <div class="form-group">
            <label class="form-label">特殊情境反应逻辑</label>
            <TagsInput v-model="draft.specialLogic" separator="、" placeholder="输入后按回车添加" />
          </div>
        </section>

        <section id="char-section-examples" class="config-section">
          <header class="section-header">
            <h3 class="section-heading">示例对话</h3>
            <p class="section-desc">Few-Shot 示例，帮助模型把握口吻</p>
          </header>
          <div class="form-group">
            <label class="form-label">Few-Shot 示例对话</label>
            <ConversationPairInput v-model="draft.fewShotExamples" />
          </div>
        </section>
      </div>
    </div>

    <div v-else class="character-empty">
      <p>正在加载角色…</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useAccountStore } from '@/stores'
import type { AccountCharacter } from '@/types/character'
import { nestedCharacterToFlat } from '@/utils/character-card-mapper'
import { characterCardsApi } from '@/api/character-cards'
import { useToast } from '@/composables/useToast'
import { logger } from '@/utils/logger'
import AutoResizeTextarea from '@/components/common/AutoResizeTextarea.vue'
import TagsInput from '@/components/common/TagsInput.vue'
import ConversationPairInput from '@/components/common/ConversationPairInput.vue'

const genderOptions = [
  { value: '男', label: '男', icon: '♂' },
  { value: '女', label: '女', icon: '♀' },
  { value: '中性', label: '中性', icon: '⚪' },
]

const props = defineProps<{
  characterId?: string | null
}>()

const emit = defineEmits<{
  (e: 'character-loaded', characterId: string): void
}>()

const accountStore = useAccountStore()
const toast = useToast()

const draft = ref<AccountCharacter | null>(null)
const saving = ref(false)
const isSaving = computed(() => saving.value)
const baselineJson = ref<string | null>(null)

const emotionRules = ref({
  emoji: true,
  modalParticles: true,
  punctuationEmotion: true,
})

function parseEmotionRules(value: string) {
  const rules = {
    emoji: true,
    modalParticles: true,
    punctuationEmotion: true,
  }

  if (!value) return rules

  const emojiMatch = value.match(/【表情符号：([^】]+)】/)
  const modalMatch = value.match(/【语气词：([^】]+)】/)
  const punctuationMatch = value.match(/【标点符号表达情绪：([^】]+)】/)

  if (emojiMatch) {
    rules.emoji = emojiMatch[1].includes('允许')
  }
  if (modalMatch) {
    rules.modalParticles = modalMatch[1].includes('允许')
  }
  if (punctuationMatch) {
    rules.punctuationEmotion = punctuationMatch[1].includes('允许')
  }

  return rules
}

function updateEmotionRules() {
  if (!draft.value) return

  const parts: string[] = []
  parts.push(`【表情符号：${emotionRules.value.emoji ? '允许使用' : '禁止使用'}】`)
  parts.push(`【语气词：${emotionRules.value.modalParticles ? '允许使用' : '禁止使用'}】`)
  parts.push(
    `【标点符号表达情绪：${emotionRules.value.punctuationEmotion ? '允许使用' : '禁止使用'}】`
  )

  draft.value.communication.emotionRules = parts.join('')
}

watch(
  () => draft.value?.communication.emotionRules,
  newVal => {
    if (newVal !== undefined) {
      emotionRules.value = parseEmotionRules(newVal)
    }
  },
  { immediate: true }
)

const scrollEl = ref<HTMLElement | null>(null)
const activeSection = ref('basic')

const sectionNav = [
  { id: 'basic', label: '基础档案' },
  { id: 'personality', label: '性格认知' },
  { id: 'language', label: '语言风格' },
  { id: 'scenarios', label: '情境反应' },
  { id: 'examples', label: '示例对话' },
]

function cloneChar<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj)) as T
}

function captureBaseline(): void {
  if (draft.value) {
    baselineJson.value = JSON.stringify(draft.value)
  }
}

async function syncToServer(char: AccountCharacter): Promise<void> {
  if (!accountStore.currentAccount) return
  const uid = accountStore.currentAccount.id
  const flat = nestedCharacterToFlat(char, uid)
  await characterCardsApi.upsert(uid, char.id, flat)
}

async function findCharacter(targetCharacterId?: string): Promise<AccountCharacter | null> {
  const list = await accountStore.loadCharacters()
  const aid = targetCharacterId ?? accountStore.currentConfig?.activeCharacterId

  let char: AccountCharacter | null = aid
    ? ((await accountStore.getCharacter(aid)) as AccountCharacter | null)
    : null

  if (!char && list.length > 0) {
    char = list[0]
    await accountStore.setActiveCharacterId(char.id)
  }

  return char
}

async function loadCharacter(targetCharacterId?: string): Promise<void> {
  if (!accountStore.currentAccount) {
    draft.value = null
    return
  }

  await accountStore.loadCurrentAccountData()
  const char = await findCharacter(targetCharacterId)

  if (!char) {
    logger.info('CharacterSettings', 'No characters found, user can create one later')
    draft.value = null
    return
  }

  draft.value = cloneChar(char)
  captureBaseline()
  emit('character-loaded', char.id)
}

function validateCharacter(): string | null {
  if (!draft.value) return '角色数据未加载'

  if (!draft.value.name?.trim()) {
    return '请填写正式名'
  }

  if (!draft.value.roleOverview?.trim() || draft.value.roleOverview.trim().length < 10) {
    return '角色概述至少需要 10 个字符'
  }

  return null
}

async function save(): Promise<void> {
  if (!draft.value || !accountStore.currentAccount) return

  const validationError = validateCharacter()
  if (validationError) {
    toast.error(validationError)
    return
  }

  saving.value = true
  try {
    draft.value.updatedAt = new Date().toISOString()
    await accountStore.saveCharacter(draft.value)
    try {
      await syncToServer(draft.value)
      toast.success('已保存并同步到服务端')
    } catch (e) {
      logger.error('CharacterSettings', 'Server sync failed', e)
      toast.warning('已保存到本地，同步服务器失败，请稍后重试')
    }
    captureBaseline()
  } finally {
    saving.value = false
  }
}

function reset(): void {
  if (!baselineJson.value) {
    void loadCharacter()
    toast.info('已重新加载')
    return
  }
  try {
    draft.value = cloneChar(JSON.parse(baselineJson.value) as AccountCharacter)
    toast.success('已重置为上次保存内容')
  } catch {
    void loadCharacter()
  }
}

function exportJson(): void {
  if (!draft.value || !accountStore.currentAccount) return

  const payload = {
    version: '1',
    exportedAt: new Date().toISOString(),
    accountId: accountStore.currentAccount.id,
    character: draft.value,
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: 'application/json',
  })
  const safeName = (draft.value.name || 'character').replace(/[/\\?%*:|"<>]/g, '_')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `character-${safeName}-${draft.value.id.slice(-8)}.json`
  a.click()
  URL.revokeObjectURL(a.href)
  toast.success('已导出 JSON')
}

function scrollToSection(id: string): void {
  const el = document.getElementById(`char-section-${id}`)
  el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  activeSection.value = id
}

onMounted(() => {
  void loadCharacter(props.characterId ?? undefined)
})

watch(
  () => accountStore.currentAccountId,
  () => {
    void loadCharacter(props.characterId ?? undefined)
  }
)

watch(
  () => props.characterId,
  newId => {
    if (newId) {
      void loadCharacter(newId)
    }
  }
)

async function resetToDefault(): Promise<void> {
  if (!accountStore.currentAccount) return

  const defaultChar = accountStore.createBlankCharacter()
  if (draft.value) {
    defaultChar.id = draft.value.id
    defaultChar.createdAt = draft.value.createdAt
    defaultChar.updatedAt = new Date().toISOString()
  }

  draft.value = defaultChar
  captureBaseline()
  await save()
}

defineExpose({
  loadCharacter,
  save,
  reset,
  resetToDefault,
  exportJson,
  isSaving,
})
</script>

<style scoped lang="scss">
.character-settings {
  min-height: 200px;
}

.config-root {
  display: flex;
  gap: 20px;
  align-items: stretch;
  min-height: 0;
}

.section-nav {
  width: 180px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: linear-gradient(180deg, #fafafa 0%, #ffffff 100%);
  align-self: flex-start;
  position: sticky;
  top: 0;
  max-height: min(72vh, 640px);
  overflow-y: auto;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 2px;
  }
}

.section-nav-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 10px 14px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font-size: 17px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 400;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%) scaleY(0);
    width: 3px;
    height: 20px;
    background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
    border-radius: 0 2px 2px 0;
    transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  &:hover {
    background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
    color: #374151;
    transform: translateX(2px);
  }

  &.active {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    color: #1d4ed8;
    font-weight: 600;

    &::before {
      transform: translateY(-50%) scaleY(1);
    }
  }
}

.config-scroll {
  flex: 1;
  min-width: 0;
  max-height: min(72vh, 640px);
  overflow-y: auto;
  padding-right: 8px;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #f8fafc;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #cbd5e1 0%, #94a3b8 100%);
    border-radius: 4px;
    transition: all 0.2s ease;

    &:hover {
      background: linear-gradient(180deg, #94a3b8 0%, #64748b 100%);
    }
  }
}

.config-section {
  margin-bottom: 32px;
  padding-bottom: 28px;
  border-bottom: 1px solid #f1f5f9;
  animation: fadeInUp 0.4s ease-out;

  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-header {
  margin-bottom: 20px;
}

.section-heading {
  margin: 0 0 8px;
  font-size: 21px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
  background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-desc {
  margin: 0;
  font-size: 16px;
  color: #64748b;
  line-height: 1.6;
}

.section-required-note {
  margin: 8px 0 0;
  font-size: 14px;
  color: #dc2626;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #fef2f2;
  border-radius: 6px;
  border: 1px solid #fecaca;
}

.required-mark {
  color: #dc2626;
  font-weight: 700;
  font-size: 18px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 20px;
}

.form-group {
  margin-bottom: 10px;

  &.full-width {
    grid-column: 1 / -1;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 20px;
  grid-column: 1 / -1;
}

.form-label {
  display: block;
  font-size: 16px;
  color: #374151;
  margin-bottom: 8px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.form-input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 14px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 18px;
  font-family: inherit;
  background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);

  &:hover {
    border-color: #9ca3af;
    box-shadow: 0 0 0 4px rgba(148, 163, 184, 0.1);
  }

  &:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.15);
    background: #ffffff;
  }
}

.gender-selector {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}

.gender-option {
  flex: 1;
  min-width: 70px;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 10px 14px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    opacity: 0;
    transition: opacity 0.2s ease;
  }

  &:hover {
    border-color: #9ca3af;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);

    &::before {
      opacity: 0.5;
    }
  }

  &.active {
    border-color: #3b82f6;
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.15);
    transform: translateY(-2px);
  }
}

.gender-label {
  font-size: 18px;
  font-weight: 500;
  color: #374151;
  position: relative;
  z-index: 1;

  .gender-option.active & {
    color: #1d4ed8;
    font-weight: 600;
  }
}

.emotion-rules-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px 20px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
}

.emotion-rule-item {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  padding: 8px 0;
  transition: all 0.2s ease;

  &:hover {
    transform: translateX(4px);
  }
}

.emotion-rule-item input[type='checkbox'] {
  width: 22px;
  height: 22px;
  cursor: pointer;
  accent-color: #3b82f6;
  transition: all 0.2s ease;
  border-radius: 6px;

  &:hover {
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
  }
}

.emotion-rule-label {
  font-size: 18px;
  color: #374151;
  font-weight: 500;
}

.character-empty {
  padding: 48px 32px;
  text-align: center;
  color: #64748b;
  font-size: 18px;
  font-weight: 500;
}
</style>
