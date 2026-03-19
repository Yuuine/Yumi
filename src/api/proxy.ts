import type { ProxySettings } from '@/types'
import { httpClient } from './http-client'

export const proxyApi = {
  async getProxySettings(): Promise<ProxySettings> {
    return httpClient.get<ProxySettings>('/settings/proxy')
  },

  async updateProxySettings(settings: ProxySettings): Promise<ProxySettings> {
    return httpClient.put<ProxySettings>('/settings/proxy', settings)
  },

  async scanProxyPorts(): Promise<string[]> {
    return httpClient.post<string[]>('/proxy/scan')
  },
}
