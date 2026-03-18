import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { logger } from '@/utils/logger'

const STORAGE_KEY = 'yumi_settings'

interface SettingsState {
  showReasoning: boolean
  theme: 'light' | 'dark'
}

const DEFAULT_SETTINGS: SettingsState = {
  showReasoning: true,
  theme: 'light',
}

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<SettingsState>({ ...DEFAULT_SETTINGS })

  const showReasoning = computed(() => settings.value.showReasoning)
  const theme = computed(() => settings.value.theme)

  function loadSettings() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<SettingsState>
        settings.value = { ...DEFAULT_SETTINGS, ...parsed }
        logger.info('SettingsStore', 'Settings loaded', settings.value)
      }
    } catch (error) {
      logger.error('SettingsStore', 'Failed to load settings', error)
    }
  }

  function saveSettings() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings.value))
      logger.info('SettingsStore', 'Settings saved', settings.value)
    } catch (error) {
      logger.error('SettingsStore', 'Failed to save settings', error)
    }
  }

  function setShowReasoning(value: boolean) {
    settings.value.showReasoning = value
    saveSettings()
  }

  function setTheme(value: 'light' | 'dark') {
    settings.value.theme = value
    saveSettings()
  }

  function resetSettings() {
    settings.value = { ...DEFAULT_SETTINGS }
    saveSettings()
  }

  loadSettings()

  return {
    settings,
    showReasoning,
    theme,
    loadSettings,
    saveSettings,
    setShowReasoning,
    setTheme,
    resetSettings,
  }
})
