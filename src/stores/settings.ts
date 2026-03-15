import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AppSettings } from '@/types'
import { settingsApi } from '@/api/settings'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AppSettings>({
    apiEndpoint: 'http://127.0.0.1:11434/v1',
    apiKey: '',
    modelName: 'llama3.1:8b',
    maxTokens: 4096,
    temperature: 0.85,
    memoryEnabled: true,
    emotionDetection: true,
    theme: 'light',
    language: 'zh-CN',
  })

  const theme = ref<'light' | 'dark'>('light')
  const isLoading = ref(false)
  const isLoaded = ref(false)

  async function loadSettings() {
    if (isLoaded.value) return
    isLoading.value = true
    try {
      const loaded = await settingsApi.getSettings()
      settings.value = loaded
      theme.value = loaded.theme
      isLoaded.value = true
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function updateSettings(newSettings: Partial<AppSettings>) {
    isLoading.value = true
    try {
      const updated = await settingsApi.updateSettings({
        ...settings.value,
        ...newSettings,
      })
      settings.value = updated
      if (newSettings.theme) {
        theme.value = newSettings.theme
      }
      return updated
    } catch (error) {
      console.error('Failed to update settings:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function setTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
    updateSettings({ theme: newTheme })
  }

  return {
    settings,
    theme,
    isLoading,
    loadSettings,
    updateSettings,
    setTheme,
  }
})
