import type { UserProfile } from '@/types'
import type { CharacterCardFlat } from '@/types/character'
import { httpClient } from './http-client'

export interface UserListItem {
  id: string
  roleName: string
  createdAt: string
  updatedAt: string
}

export interface ListUsersResponse {
  users: UserListItem[]
}

export interface FullAccountData {
  id: string
  roleName: string
  preferences: {
    communicationStyle: string
    topicsOfInterest: string[]
    emotionalSupportLevel: string
    responseLength: string
  }
  createdAt: string
  updatedAt: string
  characterCards: CharacterCardFlat[]
  conversations: Array<{
    id: string
    user_id: string
    character_id: string | null
    title: string | null
    created_at: string
    updated_at: string
    is_active: number
    character_name?: string
    formal_name?: string
  }>
}

interface PurgeUserResponse {
  success: boolean
  cleared: Record<string, number>
}

export const userApi = {
  async listUsers(): Promise<ListUsersResponse> {
    return httpClient.get<ListUsersResponse>('/user/list')
  },

  async getFullAccountData(userId: string): Promise<FullAccountData> {
    return httpClient.get<FullAccountData>(`/user/full/${encodeURIComponent(userId)}`)
  },

  async getProfile(userId: string): Promise<UserProfile> {
    return httpClient.get<UserProfile>('/user/profile', {
      params: { userId },
    })
  },

  async updateProfile(profile: UserProfile): Promise<UserProfile> {
    return httpClient.put<UserProfile>('/user/profile', profile)
  },

  async purgeUserData(userId: string): Promise<PurgeUserResponse> {
    return httpClient.post<PurgeUserResponse>('/user/purge', { userId })
  },
}
