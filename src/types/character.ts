/**
 * 本地「角色卡」嵌套结构（与 account 存储一致，为权威数据源）
 */

export interface CharacterAppearance {
  race: string
  gender: string
  visualAge: string
  actualAge: string
  location: string
  description: string
}

export interface CharacterPersonality {
  core: string
  selfPerception: string
  attitudeToUser: string
  likes: string
  dislikes: string
}

export interface CharacterCommunication {
  toneBase: string
  wordHabits: string
  emotionRules: string
  lengthPref: string
}

export interface AccountCharacter {
  id: string
  accountId?: string
  name: string
  nickname: string
  isActive?: boolean
  roleOverview: string
  appearance: CharacterAppearance
  personality: CharacterPersonality
  communication: CharacterCommunication
  specialLogic: string
  fewShotExamples: string
  createdAt: string
  updatedAt: string
}

/** 与后端 / DB 扁平字段一致，用于 API 同步 */
export interface CharacterCardFlat {
  id: string
  userId: string
  conversationId: string | null
  roleOverview: string
  formalName: string
  nickname: string
  raceOrForm: string
  gender: string
  visualAge: string
  actualAge: string
  location: string
  appearanceDesc: string
  corePersonality: string
  selfPerception: string
  attitudeToUser: string
  likes: string
  dislikes: string
  toneBase: string
  wordHabits: string
  emotionRules: string
  lengthPref: string
  specialLogicList: string
  fewShotExamples: string
  isActive: boolean
}
