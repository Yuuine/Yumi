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
          </header>
          <div class="form-grid">
            <div class="form-group">
              <label class="form-label">正式名</label>
              <input v-model="draft.name" class="form-input" type="text" maxlength="30" />
            </div>
            <div class="form-group">
              <label class="form-label">昵称</label>
              <input v-model="draft.nickname" class="form-input" type="text" />
            </div>
            <div class="form-group full-width">
              <label class="form-label">角色概述</label>
              <textarea v-model="draft.roleOverview" class="form-textarea" rows="3" />
            </div>
            <div class="form-group">
              <label class="form-label">种族/形式</label>
              <input v-model="draft.appearance.race" class="form-input" type="text" />
            </div>
            <div class="form-group">
              <label class="form-label">性别</label>
              <input v-model="draft.appearance.gender" class="form-input" type="text" />
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
              <textarea v-model="draft.appearance.description" class="form-textarea" rows="3" />
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
            <textarea v-model="draft.personality.core" class="form-textarea" rows="3" />
          </div>
          <div class="form-group">
            <label class="form-label">自我认知</label>
            <textarea v-model="draft.personality.selfPerception" class="form-textarea" rows="3" />
          </div>
          <div class="form-group">
            <label class="form-label">对用户态度</label>
            <textarea v-model="draft.personality.attitudeToUser" class="form-textarea" rows="2" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">喜好</label>
              <textarea v-model="draft.personality.likes" class="form-textarea" rows="2" />
            </div>
            <div class="form-group">
              <label class="form-label">厌恶/雷点</label>
              <textarea v-model="draft.personality.dislikes" class="form-textarea" rows="2" />
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
            <textarea v-model="draft.communication.toneBase" class="form-textarea" rows="2" />
          </div>
          <div class="form-group">
            <label class="form-label">用词习惯</label>
            <textarea v-model="draft.communication.wordHabits" class="form-textarea" rows="2" />
          </div>
          <div class="form-group">
            <label class="form-label">情感表达规则</label>
            <textarea v-model="draft.communication.emotionRules" class="form-textarea" rows="2" />
          </div>
          <div class="form-group">
            <label class="form-label">对话长度偏好</label>
            <textarea v-model="draft.communication.lengthPref" class="form-textarea" rows="2" />
          </div>
        </section>

        <section id="char-section-scenarios" class="config-section">
          <header class="section-header">
            <h3 class="section-heading">特殊情境反应</h3>
            <p class="section-desc">特定场景下的行为与回复逻辑</p>
          </header>
          <div class="form-group">
            <label class="form-label">特殊情境反应逻辑</label>
            <textarea v-model="draft.specialLogic" class="form-textarea" rows="5" />
          </div>
        </section>

        <section id="char-section-examples" class="config-section">
          <header class="section-header">
            <h3 class="section-heading">示例对话</h3>
            <p class="section-desc">Few-Shot 示例，帮助模型把握口吻</p>
          </header>
          <div class="form-group">
            <label class="form-label">Few-Shot 示例对话</label>
            <textarea v-model="draft.fewShotExamples" class="form-textarea" rows="8" />
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
/** 上次加载或保存成功后的快照，用于重置 */
const baselineJson = ref<string | null>(null)

const scrollEl = ref<HTMLElement | null>(null)
const activeSection = ref('basic')

const sectionNav = [
  { id: 'basic', label: '基础档案' },
  { id: 'personality', label: '性格认知' },
  { id: 'language', label: '语言风格' },
  { id: 'scenarios', label: '情境反应' },
  { id: 'examples', label: '示例对话' },
]

function cloneChar(c: AccountCharacter): AccountCharacter {
  return JSON.parse(JSON.stringify(c)) as AccountCharacter
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

/**
 * 加载指定角色，或者加载当前活跃角色
 */
async function loadCharacter(targetCharacterId?: string): Promise<void> {
  if (!accountStore.currentAccount) {
    draft.value = null
    return
  }

  await accountStore.loadCurrentAccountData()

  const list = await accountStore.loadCharacters()
  let char: AccountCharacter | null = null
  const aid = targetCharacterId || accountStore.currentConfig?.activeCharacterId

  if (aid) {
    char = (await accountStore.getCharacter(aid)) as AccountCharacter | null
  }
  if (!char && list.length > 0) {
    char = list[0]
    await accountStore.setActiveCharacterId(char.id)
  }
  if (!char) {
    const t = accountStore.createNewCharacterTemplate()
    await accountStore.saveCharacter(t)
    await accountStore.setActiveCharacterId(t.id)
    char = t
    try {
      await syncToServer(t)
    } catch (e) {
      logger.warn('CharacterSettings', 'Initial sync failed', { error: String(e) })
    }
  }

  draft.value = cloneChar(char)
  captureBaseline()
  emit('character-loaded', char.id)
}

async function save(): Promise<void> {
  if (!draft.value || !accountStore.currentAccount) return
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

defineExpose({
  loadCharacter,
  save,
  reset,
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
  gap: 16px;
  align-items: stretch;
  min-height: 0;
}

.section-nav {
  width: 168px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fafafa;
  align-self: flex-start;
  position: sticky;
  top: 0;
  max-height: min(72vh, 640px);
  overflow-y: auto;
}

.section-nav-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: #f3f4f6;
  }

  &.active {
    background: #eff6ff;
    color: #1d4ed8;
    font-weight: 500;
  }
}

.config-scroll {
  flex: 1;
  min-width: 0;
  max-height: min(72vh, 640px);
  overflow-y: auto;
  padding-right: 4px;
}

.config-section {
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f3f4f6;

  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }
}

.section-header {
  margin-bottom: 16px;
}

.section-heading {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.section-desc {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
}

.form-group {
  margin-bottom: 0;

  &.full-width {
    grid-column: 1 / -1;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
  grid-column: 1 / -1;
}

.form-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.form-input,
.form-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  background: #fff;

  &:focus {
    outline: none;
    border-color: #93c5fd;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
  }
}

.form-textarea {
  resize: vertical;
  min-height: 64px;
}

.character-empty {
  padding: 32px;
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
}
</style>
