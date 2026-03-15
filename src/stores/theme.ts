import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

export type Theme = 'light' | 'dark'

const THEME_KEY = 'yumi-theme'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<Theme>((localStorage.getItem(THEME_KEY) as Theme) || 'light')

  function setTheme(newTheme: Theme): void {
    theme.value = newTheme
    localStorage.setItem(THEME_KEY, newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  function initTheme(): void {
    const savedTheme = localStorage.getItem(THEME_KEY) as Theme
    if (savedTheme) {
      theme.value = savedTheme
      document.documentElement.setAttribute('data-theme', savedTheme)
    }
  }

  watch(theme, newTheme => {
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem(THEME_KEY, newTheme)
  })

  return {
    theme,
    setTheme,
    initTheme,
  }
})

export const useTheme = () => {
  const themeStore = useThemeStore()
  return {
    theme: themeStore.theme,
    isDark: computed(() => themeStore.theme === 'dark'),
    setTheme: themeStore.setTheme,
  }
}
