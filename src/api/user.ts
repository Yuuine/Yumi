import type { UserProfile } from '@/types'
import { httpClient } from './http-client'

export const userApi = {
  async getProfile(userId: string): Promise<UserProfile> {
    return httpClient.get<UserProfile>('/user/profile', {
      params: { userId },
    })
  },

  async updateProfile(profile: UserProfile): Promise<UserProfile> {
    return httpClient.put<UserProfile>('/user/profile', profile)
  },
}
