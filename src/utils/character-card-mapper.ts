import type { AccountCharacter, CharacterCardFlat } from '@/types/character'

/** 嵌套结构 → 扁平 DTO（camelCase，供前端 API 层转 JSON） */
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

/** 后端返回的 snake_case 或扁平 camelCase → 嵌套 AccountCharacter */
export function flatToNestedCharacter(
  flat: CharacterCardFlat & Record<string, unknown>,
  existing?: Partial<AccountCharacter>
): AccountCharacter {
  const g = (k: string) => {
    const v = flat[k as keyof typeof flat]
    return typeof v === 'string' ? v : ''
  }
  const roleOverview = g('roleOverview') || g('role_overview')
  const formalName = g('formalName') || g('formal_name')
  const raceOrForm = g('raceOrForm') || g('race_or_form')
  const visualAge = g('visualAge') || g('visual_age')
  const actualAge = g('actualAge') || g('actual_age')
  const appearanceDesc = g('appearanceDesc') || g('appearance_desc')
  const corePersonality = g('corePersonality') || g('core_personality')
  const selfPerception = g('selfPerception') || g('self_perception')
  const attitudeToUser = g('attitudeToUser') || g('attitude_to_user')
  const toneBase = g('toneBase') || g('tone_base')
  const wordHabits = g('wordHabits') || g('word_habits')
  const emotionRules = g('emotionRules') || g('emotion_rules')
  const lengthPref = g('lengthPref') || g('length_pref')
  const specialLogicList = g('specialLogicList') || g('special_logic_list')
  const fewShotExamples = g('fewShotExamples') || g('few_shot_examples')

  const id = String(flat.id || existing?.id || '')
  const now = new Date().toISOString()

  return {
    id,
    accountId: existing?.accountId,
    name: formalName || existing?.name || '',
    nickname: g('nickname') || existing?.nickname || '',
    isActive: flat.isActive ?? existing?.isActive ?? true,
    roleOverview: roleOverview || existing?.roleOverview || '',
    appearance: {
      race: raceOrForm || existing?.appearance?.race || '',
      gender: g('gender') || existing?.appearance?.gender || '',
      visualAge: visualAge || existing?.appearance?.visualAge || '',
      actualAge: actualAge || existing?.appearance?.actualAge || '',
      location: g('location') || existing?.appearance?.location || '',
      description: appearanceDesc || existing?.appearance?.description || '',
    },
    personality: {
      core: corePersonality || existing?.personality?.core || '',
      selfPerception: selfPerception || existing?.personality?.selfPerception || '',
      attitudeToUser: attitudeToUser || existing?.personality?.attitudeToUser || '',
      likes: g('likes') || existing?.personality?.likes || '',
      dislikes: g('dislikes') || existing?.personality?.dislikes || '',
    },
    communication: {
      toneBase: toneBase || existing?.communication?.toneBase || '',
      wordHabits: wordHabits || existing?.communication?.wordHabits || '',
      emotionRules: emotionRules || existing?.communication?.emotionRules || '',
      lengthPref: lengthPref || existing?.communication?.lengthPref || '',
    },
    specialLogic: specialLogicList || existing?.specialLogic || '',
    fewShotExamples: fewShotExamples || existing?.fewShotExamples || '',
    createdAt: (existing?.createdAt as string) || now,
    updatedAt: now,
  }
}
