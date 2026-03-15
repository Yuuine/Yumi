import axios, { type AxiosError, type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

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
        this.handleGlobalError(apiError)
        return Promise.reject(apiError)
      }
    )
  }

  private normalizeError(error: AxiosError<ApiErrorResponse>): ApiError {
    if (error.response?.data?.error) {
      return error.response.data.error
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

  private handleGlobalError(error: ApiError): void {
    const silentErrors = ['VALIDATION_ERROR']
    if (silentErrors.includes(error.code)) {
      return
    }

    ElMessage({
      message: error.message,
      type: 'error',
      duration: 5000,
    })
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
