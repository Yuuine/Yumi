import type { AccountCharacter, CharacterCardFlat } from '@/types/character'
import { toCamelCase } from './field-mapper'

/**
 * 嵌套结构 AccountCharacter → 扁平 DTO CharacterCardFlat
 * 用于前端内部数据转换为 API 请求格式
 */
export function nestedCharacterToFlat(char: AccountCharacter, userId: string): CharacterCardFlat {
  return {
    id: char.id,
    userId,
    conversationId: null,
    roleOverview: char.roleOverview ?? '',
    formalName: char.name ?? '',
    nickname: char.nickname ?? '',
    raceOrForm: char.appearance?.race ?? '',
    gender: char.appearance?.gender ?? '',
    visualAge: char.appearance?.visualAge ?? '',
    actualAge: char.appearance?.actualAge ?? '',
    location: char.appearance?.location ?? '',
    appearanceDesc: char.appearance?.description ?? '',
    corePersonality: char.personality?.core ?? '',
    selfPerception: char.personality?.selfPerception ?? '',
    attitudeToUser: char.personality?.attitudeToUser ?? '',
    likes: char.personality?.likes ?? '',
    dislikes: char.personality?.dislikes ?? '',
    toneBase: char.communication?.toneBase ?? '',
    wordHabits: char.communication?.wordHabits ?? '',
    emotionRules: char.communication?.emotionRules ?? '',
    lengthPref: char.communication?.lengthPref ?? '',
    specialLogicList: char.specialLogic ?? '',
    fewShotExamples: char.fewShotExamples ?? '',
    isActive: char.isActive !== false,
  }
}

/**
 * 扁平 DTO CharacterCardFlat → 嵌套结构 AccountCharacter
 * 用于后端响应数据转换为前端内部格式
 *
 * 兼容后端返回的 snake_case 和前端使用的 camelCase 字段名
 */
export function flatToNestedCharacter(
  flat: Record<string, unknown>,
  existing?: Partial<AccountCharacter>
): AccountCharacter {
  // 统一转换为 camelCase
  const data = toCamelCase(flat) as Record<string, unknown>

  const g = (key: string, fallback = ''): string => {
    const v = data[key]
    return typeof v === 'string' ? v : fallback
  }

  const id = String(data.id || existing?.id || '')
  const now = new Date().toISOString()

  return {
    id,
    accountId: existing?.accountId,
    name: g('formalName') || existing?.name || '',
    nickname: g('nickname') || existing?.nickname || '',
    isActive: (data.isActive as boolean) ?? existing?.isActive ?? true,
    roleOverview: g('roleOverview') || existing?.roleOverview || '',
    appearance: {
      race: g('raceOrForm') || existing?.appearance?.race || '',
      gender: g('gender') || existing?.appearance?.gender || '',
      visualAge: g('visualAge') || existing?.appearance?.visualAge || '',
      actualAge: g('actualAge') || existing?.appearance?.actualAge || '',
      location: g('location') || existing?.appearance?.location || '',
      description: g('appearanceDesc') || existing?.appearance?.description || '',
    },
    personality: {
      core: g('corePersonality') || existing?.personality?.core || '',
      selfPerception: g('selfPerception') || existing?.personality?.selfPerception || '',
      attitudeToUser: g('attitudeToUser') || existing?.personality?.attitudeToUser || '',
      likes: g('likes') || existing?.personality?.likes || '',
      dislikes: g('dislikes') || existing?.personality?.dislikes || '',
    },
    communication: {
      toneBase: g('toneBase') || existing?.communication?.toneBase || '',
      wordHabits: g('wordHabits') || existing?.communication?.wordHabits || '',
      emotionRules: g('emotionRules') || existing?.communication?.emotionRules || '',
      lengthPref: g('lengthPref') || existing?.communication?.lengthPref || '',
    },
    specialLogic: g('specialLogicList') || existing?.specialLogic || '',
    fewShotExamples: g('fewShotExamples') || existing?.fewShotExamples || '',
    createdAt: (existing?.createdAt as string) || now,
    updatedAt: now,
  }
}
