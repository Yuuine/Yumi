import axios, { type AxiosError, type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { error } from '@/composables/useToast'
import router from '@/router'

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
  requestId?: string
}

export interface ApiErrorResponse {
  success: false
  error: ApiError
}

// 处理未授权跳转
function handleUnauthorized(): void {
  // 清除本地存储的认证信息
  localStorage.removeItem('yumi_access_token')
  localStorage.removeItem('yumi_refresh_token')
  localStorage.removeItem('yumi_user_id')

  // 如果当前不在登录页，则跳转到登录页
  if (router.currentRoute.value.path !== '/login') {
    router.push('/login')
  }
}

export class HttpClient {
  private instance: AxiosInstance

  constructor(config?: AxiosRequestConfig) {
    this.instance = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
      ...config,
    })

    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    this.instance.interceptors.request.use(
      config => {
        const accessToken = localStorage.getItem('yumi_access_token')
        if (accessToken) {
          config.headers.Authorization = `Bearer ${accessToken}`
        }
        return config
      },
      error => {
        return Promise.reject(error)
      }
    )

    this.instance.interceptors.response.use(
      response => {
        return response
      },
      (error: AxiosError<ApiErrorResponse>) => {
        const apiError = this.normalizeError(error)

        // 处理 401 未授权和 403 拒绝访问，自动跳转到登录页
        if (error.response?.status === 401 || error.response?.status === 403) {
          handleUnauthorized()
        }

        this.handleGlobalError(apiError)
        return Promise.reject(apiError)
      }
    )
  }

  private normalizeError(error: AxiosError<unknown>): ApiError {
    // 处理标准错误格式 { error: { message, code } }
    const data = error.response?.data as Record<string, unknown>
    if (data?.error) {
      return data.error as ApiError
    }

    // 处理后端直接返回的错误格式 { message, code } 或 { detail: { message, code } }
    if (data) {
      // FastAPI 的 HTTPException 可能返回 { detail: ... }
      if (data.detail) {
        if (typeof data.detail === 'string') {
          return {
            code: 'HTTP_ERROR',
            message: data.detail,
          }
        }
        const detail = data.detail as Record<string, unknown>
        if (detail.message) {
          return {
            code: (detail.code as string) || 'HTTP_ERROR',
            message: detail.message as string,
          }
        }
      }
      // 直接返回的对象格式
      if (data.message) {
        return {
          code: (data.code as string) || 'HTTP_ERROR',
          message: data.message as string,
        }
      }
    }

    if (error.response) {
      const status = error.response.status
      const statusText = error.response.statusText

      const errorMessages: Record<number, string> = {
        400: '请求参数错误',
        401: '未授权，请重新登录',
        403: '拒绝访问',
        404: '请求的资源不存在',
        422: '数据验证失败',
        429: '请求过于频繁，请稍后再试',
        500: '服务器内部错误',
        502: '网关错误',
        503: '服务暂不可用',
        504: '网关超时',
      }

      return {
        code: `HTTP_${status}`,
        message: errorMessages[status] || statusText || '请求失败',
        details: { status, statusText },
      }
    }

    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return {
        code: 'TIMEOUT',
        message: '请求超时，请稍后再试',
      }
    }

    if (error.message === 'Network Error') {
      return {
        code: 'NETWORK_ERROR',
        message: '网络连接失败，请检查网络',
      }
    }

    return {
      code: 'UNKNOWN_ERROR',
      message: error.message || '未知错误',
    }
  }

  private handleGlobalError(apiError: ApiError): void {
    const silentErrors = ['VALIDATION_ERROR']
    if (silentErrors.includes(apiError.code)) {
      return
    }

    error(apiError.message, { duration: 5000 })
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config)
    return response.data
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config)
    return response.data
  }
}

export const httpClient = new HttpClient()
