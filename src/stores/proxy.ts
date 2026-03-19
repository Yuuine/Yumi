import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ProxySettings } from '@/types'
import { proxyApi } from '@/api/proxy'
import { logger } from '@/utils/logger'

const DEFAULT_PROXY_SETTINGS: ProxySettings = {
  enabled: false,
  mode: 'smart',
  smartSubMode: 'auto',
  manualProxyHost: '',
  manualProxyPort: 7890,
  scannedProxies: [],
  normalProxyUrl: '',
}

export const useProxyStore = defineStore('proxy', () => {
  const proxySettings = ref<ProxySettings>({ ...DEFAULT_PROXY_SETTINGS })
  const isLoading = ref(false)
  const isScanning = ref(false)

  async function loadProxySettings(): Promise<void> {
    isLoading.value = true
    try {
      const data = await proxyApi.getProxySettings()
      proxySettings.value = { ...DEFAULT_PROXY_SETTINGS, ...data }
      logger.info('ProxyStore', 'Proxy settings loaded', proxySettings.value)
    } catch (error) {
      logger.error('ProxyStore', 'Failed to load proxy settings', error)
      proxySettings.value = { ...DEFAULT_PROXY_SETTINGS }
    } finally {
      isLoading.value = false
    }
  }

  async function saveProxySettings(settings: ProxySettings): Promise<void> {
    isLoading.value = true
    try {
      const data = await proxyApi.updateProxySettings(settings)
      proxySettings.value = { ...data }
      logger.info('ProxyStore', 'Proxy settings saved', proxySettings.value)
    } catch (error) {
      logger.error('ProxyStore', 'Failed to save proxy settings', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function scanProxyPorts(): Promise<string[]> {
    isScanning.value = true
    try {
      const proxies = await proxyApi.scanProxyPorts()
      proxySettings.value = {
        ...proxySettings.value,
        scannedProxies: proxies,
      }
      logger.info('ProxyStore', 'Proxy scan completed', { count: proxies.length })
      return proxies
    } catch (error) {
      logger.error('ProxyStore', 'Proxy scan failed', error)
      throw error
    } finally {
      isScanning.value = false
    }
  }

  return {
    proxySettings,
    isLoading,
    isScanning,
    loadProxySettings,
    saveProxySettings,
    scanProxyPorts,
  }
})
