import type { UserProfile } from '@/types'
import { httpClient } from './http-client'

interface PurgeUserResponse {
  success: boolean
  cleared: Record<string, number>
}

export const userApi = {
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
