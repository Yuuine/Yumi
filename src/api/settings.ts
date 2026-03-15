import type { AppSettings } from '@/types'
import { httpClient } from './http-client'

export const settingsApi = {
  async getSettings(): Promise<AppSettings> {
    return httpClient.get<AppSettings>('/settings')
  },

  async updateSettings(settings: AppSettings): Promise<AppSettings> {
    return httpClient.put<AppSettings>('/settings', settings)
  },
}
