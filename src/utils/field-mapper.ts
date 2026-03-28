/**
 * 字段映射工具 - 前后端命名规范转换
 *
 * 前端: 驼峰命名 (camelCase) - userId, characterId
 * 后端: 蛇形命名 (snake_case) - user_id, character_id
 */

function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
}

function convertKeys<T extends object>(obj: T, converter: (key: string) => string): T {
  if (obj === null || obj === undefined) {
    return obj
  }

  if (Array.isArray(obj)) {
    return obj.map(item =>
      typeof item === 'object' && item !== null ? convertKeys(item, converter) : item
    ) as T
  }

  if (typeof obj === 'object') {
    const result: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(obj)) {
      const newKey = converter(key)
      if (
        value !== null &&
        value !== undefined &&
        typeof value === 'object' &&
        !Array.isArray(value)
      ) {
        result[newKey] = convertKeys(value as Record<string, unknown>, converter)
      } else if (Array.isArray(value)) {
        result[newKey] = value.map(item =>
          typeof item === 'object' && item !== null
            ? convertKeys(item as Record<string, unknown>, converter)
            : item
        )
      } else {
        result[newKey] = value
      }
    }
    return result as T
  }

  return obj
}

export function toCamelCase<T extends object>(obj: T): T {
  return convertKeys(obj, snakeToCamel)
}

export function toSnakeCase<T extends object>(obj: T): T {
  return convertKeys(obj, camelToSnake)
}

export function toCamelCaseStr(str: string): string {
  return snakeToCamel(str)
}

export function toSnakeCaseStr(str: string): string {
  return camelToSnake(str)
}

export interface ConversationDTO {
  id: string
  userId?: string
  characterId?: string | null
  title?: string | null
  isActive?: boolean
  createdAt?: string
  updatedAt?: string
}

export function toConversationDTO(raw: Record<string, unknown>): ConversationDTO {
  return {
    id: String(raw.id ?? ''),
    userId: raw.user_id as string | undefined,
    characterId: raw.character_id as string | null | undefined,
    title: raw.title as string | null | undefined,
    isActive: raw.is_active as boolean | undefined,
    createdAt: raw.created_at as string | undefined,
    updatedAt: raw.updated_at as string | undefined,
  }
}

export function toConversationListDTO(rawList: Record<string, unknown>[]): ConversationDTO[] {
  return rawList.map(item => toConversationDTO(item))
}

export function conversationToBackend(data: Partial<ConversationDTO>): Record<string, unknown> {
  const result: Record<string, unknown> = {}

  if (data.id !== undefined) result.id = data.id
  if (data.userId !== undefined) result.user_id = data.userId
  if (data.characterId !== undefined) result.character_id = data.characterId
  if (data.title !== undefined) result.title = data.title
  if (data.isActive !== undefined) result.is_active = data.isActive
  if (data.createdAt !== undefined) result.created_at = data.createdAt
  if (data.updatedAt !== undefined) result.updated_at = data.updatedAt

  return result
}

export interface CharacterCardDTO {
  id: string
  userId?: string
  conversationId?: string | null
  roleOverview?: string
  formalName?: string
  nickname?: string
  raceOrForm?: string
  gender?: string
  visualAge?: string
  actualAge?: string
  location?: string
  appearanceDesc?: string
  corePersonality?: string
  selfPerception?: string
  attitudeToUser?: string
  likes?: string
  dislikes?: string
  toneBase?: string
  wordHabits?: string
  emotionRules?: string
  lengthPref?: string
  specialLogicList?: string
  fewShotExamples?: string
  isActive?: boolean
  createdAt?: string
  updatedAt?: string
}

const CHARACTER_CARD_FIELDS: Record<string, string> = {
  id: 'id',
  userId: 'user_id',
  conversationId: 'conversation_id',
  roleOverview: 'role_overview',
  formalName: 'formal_name',
  nickname: 'nickname',
  raceOrForm: 'race_or_form',
  gender: 'gender',
  visualAge: 'visual_age',
  actualAge: 'actual_age',
  location: 'location',
  appearanceDesc: 'appearance_desc',
  corePersonality: 'core_personality',
  selfPerception: 'self_perception',
  attitudeToUser: 'attitude_to_user',
  likes: 'likes',
  dislikes: 'dislikes',
  toneBase: 'tone_base',
  wordHabits: 'word_habits',
  emotionRules: 'emotion_rules',
  lengthPref: 'length_pref',
  specialLogicList: 'special_logic_list',
  fewShotExamples: 'few_shot_examples',
  isActive: 'is_active',
  createdAt: 'created_at',
  updatedAt: 'updated_at',
}

export function toCharacterCardDTO(raw: Record<string, unknown>): CharacterCardDTO {
  const result: CharacterCardDTO = {
    id: String(raw.id ?? ''),
  }

  for (const [camel, snake] of Object.entries(CHARACTER_CARD_FIELDS)) {
    if (camel === 'id') continue
    const value = raw[snake] ?? raw[camel]
    if (value !== undefined) {
      ;(result as unknown as Record<string, unknown>)[camel] = value
    }
  }

  return result
}

export function toCharacterCardListDTO(rawList: Record<string, unknown>[]): CharacterCardDTO[] {
  return rawList.map(item => toCharacterCardDTO(item))
}

export function characterCardToBackend(data: Partial<CharacterCardDTO>): Record<string, unknown> {
  const result: Record<string, unknown> = {}

  for (const [camel, snake] of Object.entries(CHARACTER_CARD_FIELDS)) {
    const value = (data as Record<string, unknown>)[camel]
    if (value !== undefined) {
      result[snake] = value
    }
  }

  return result
}
