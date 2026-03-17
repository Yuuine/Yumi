import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UserProfile, BigFiveTraits, UserPreferences } from '@/types'
import { userApi } from '@/api/user'
import { logger } from '@/utils/logger'

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile>({
    id: 'default',
    roleName: 'Yumi',
    bigFive: {
      openness: 0.75,
      conscientiousness: 0.7,
      extraversion: 0.65,
      agreeableness: 0.8,
      neuroticism: 0.35,
    },
    preferences: {
      communicationStyle: 'warm',
      topicsOfInterest: ['生活', '工作', '情感'],
      emotionalSupportLevel: 'high',
      responseLength: 'medium',
    },
  })

  const isLoading = ref(false)
  const isLoaded = ref(false)

  async function loadProfile(userId: string = 'default') {
    if (isLoaded.value) return
    isLoading.value = true
    try {
      const loaded = await userApi.getProfile(userId)
      profile.value = loaded
      isLoaded.value = true
    } catch (error) {
      logger.error('UserStore', 'Failed to load profile', error)
    } finally {
      isLoading.value = false
    }
  }

  async function updateProfile(newProfile: Partial<UserProfile>) {
    isLoading.value = true
    try {
      const updated = await userApi.updateProfile({
        ...profile.value,
        ...newProfile,
      })
      profile.value = updated
      return updated
    } catch (error) {
      logger.error('UserStore', 'Failed to update profile', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function updateBigFive(traits: Partial<BigFiveTraits>) {
    return updateProfile({
      bigFive: {
        ...profile.value.bigFive,
        ...traits,
      },
    })
  }

  async function updatePreferences(prefs: Partial<UserPreferences>) {
    return updateProfile({
      preferences: {
        ...profile.value.preferences,
        ...prefs,
      },
    })
  }

  return {
    profile,
    isLoading,
    loadProfile,
    updateProfile,
    updateBigFive,
    updatePreferences,
  }
})
