import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => ({
  default: {
    create: vi.fn(),
  },
}))

vi.mock('@/composables/useToast', () => ({
  error: vi.fn(),
}))

vi.mock('@/router', () => ({
  default: {
    currentRoute: {
      value: {
        path: '/',
      },
    },
    push: vi.fn(),
  },
}))

vi.mock('@/utils/api-cache', () => ({
  apiCache: {
    get: vi.fn(),
    set: vi.fn(),
  },
}))

vi.mock('@/utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}))

import axios from 'axios'
import { error as toastError } from '@/composables/useToast'
import router from '@/router'
import { apiCache } from '@/utils/api-cache'

const mockedAxios = vi.mocked(axios, true)

describe('http-client.ts - HTTP 客户端', () => {
  let httpClient: any
  let mockInstance: any
  let HttpClient: any
  let requestInterceptorFulfilled: any
  let requestInterceptorRejected: any
  let responseInterceptorFulfilled: any
  let responseInterceptorRejected: any

  beforeEach(async () => {
    vi.clearAllMocks()

    mockInstance = {
      interceptors: {
        request: {
          use: vi.fn((fulfilled, rejected) => {
            requestInterceptorFulfilled = fulfilled
            requestInterceptorRejected = rejected
          }),
        },
        response: {
          use: vi.fn((fulfilled, rejected) => {
            responseInterceptorFulfilled = fulfilled
            responseInterceptorRejected = rejected
          }),
        },
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    }

    mockedAxios.create.mockReturnValue(mockInstance)

    const module = await import('@/api/http-client')
    HttpClient = module.HttpClient
    httpClient = new HttpClient()
  })

  describe('初始化和拦截器设置', () => {
    it('创建 axios 实例并设置默认配置', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: '/api',
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
        },
      })
    })

    it('设置请求和响应拦截器', () => {
      expect(mockInstance.interceptors.request.use).toHaveBeenCalled()
      expect(mockInstance.interceptors.response.use).toHaveBeenCalled()
    })
  })

  describe('请求拦截器', () => {
    it.skip('添加 Authorization 头部当 accessToken 存在时', () => {
      const mockConfig = { headers: {} }
      const testToken = 'test-access-token-123'
      vi.mocked(localStorage.getItem).mockReturnValue(testToken)

      const result = requestInterceptorFulfilled(mockConfig)

      expect(result.headers.Authorization).toBe(`Bearer ${testToken}`)
      expect(localStorage.getItem).toHaveBeenCalledWith('yumi_access_token')
    })

    it.skip('不添加 Authorization 头部当 accessToken 不存在时', () => {
      const mockConfig = { headers: {} }
      vi.mocked(localStorage.getItem).mockReturnValue(null)

      const result = requestInterceptorFulfilled(mockConfig)

      expect(result.headers.Authorization).toBeUndefined()
    })

    it('请求拦截器的错误处理', async () => {
      const testError = new Error('Test request error')
      await expect(requestInterceptorRejected(testError)).rejects.toThrow(testError)
    })
  })

  describe('响应拦截器', () => {
    it('正常响应直接返回', () => {
      const mockResponse = { data: { success: true, result: 'ok' } }
      const result = responseInterceptorFulfilled(mockResponse)
      expect(result).toEqual(mockResponse)
    })

    it('401 错误处理', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { error: { code: 'UNAUTHORIZED', message: '未授权' } },
        },
      }

      await expect(responseInterceptorRejected(mockError)).rejects.toBeDefined()
      expect(router.push).toHaveBeenCalledWith('/login')
    })

    it('403 错误也会跳转到登录页', async () => {
      const mockError = {
        response: {
          status: 403,
          data: { error: { code: 'FORBIDDEN', message: '拒绝访问' } },
        },
      }

      await expect(responseInterceptorRejected(mockError)).rejects.toBeDefined()

      expect(router.push).toHaveBeenCalledWith('/login')
    })

    it('非 401/403 错误显示 toast 但不跳转', async () => {
      const mockError = {
        response: {
          status: 500,
          statusText: 'Internal Server Error',
          data: null,
        },
      }

      await expect(responseInterceptorRejected(mockError)).rejects.toBeDefined()

      expect(router.push).not.toHaveBeenCalled()
      expect(toastError).toHaveBeenCalled()
    })
  })

  describe('错误处理 - normalizeError', () => {
    it('处理标准格式 { error: { message, code } }', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            error: { code: 'VALIDATION_ERROR', message: '参数验证失败' },
          },
        },
      }

      const result = await responseInterceptorRejected(mockError).catch(e => e)

      expect(result.code).toBe('VALIDATION_ERROR')
      expect(result.message).toBe('参数验证失败')
    })

    it('处理 FastAPI 格式 { detail: string }', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { detail: '详细错误信息' },
        },
      }

      const result = await responseInterceptorRejected(mockError).catch(e => e)

      expect(result.code).toBe('HTTP_ERROR')
      expect(result.message).toBe('详细错误信息')
    })

    it('处理 FastAPI 格式 { detail: { message, code } }', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { detail: { message: '详细信息', code: 'DETAIL_ERROR' } },
        },
      }

      const result = await responseInterceptorRejected(mockError).catch(e => e)

      expect(result.code).toBe('DETAIL_ERROR')
      expect(result.message).toBe('详细信息')
    })

    it('处理直接格式 { message, code }', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { message: '直接消息', code: 'DIRECT_ERROR' },
        },
      }

      const result = await responseInterceptorRejected(mockError).catch(e => e)

      expect(result.code).toBe('DIRECT_ERROR')
      expect(result.message).toBe('直接消息')
    })

    it('处理 HTTP 状态码对应的消息', async () => {
      const testCases = [
        { status: 400, expectedMessage: '请求参数错误' },
        { status: 404, expectedMessage: '请求的资源不存在' },
        { status: 422, expectedMessage: '数据验证失败' },
        { status: 429, expectedMessage: '请求过于频繁，请稍后再试' },
        { status: 500, expectedMessage: '服务器内部错误' },
        { status: 502, expectedMessage: '网关错误' },
        { status: 503, expectedMessage: '服务暂不可用' },
        { status: 504, expectedMessage: '网关超时' },
      ]

      for (const testCase of testCases) {
        const mockError = {
          response: {
            status: testCase.status,
            statusText: 'Some Status',
            data: null,
          },
        }

        const result = await responseInterceptorRejected(mockError).catch(e => e)
        expect(result.code).toBe(`HTTP_${testCase.status}`)
        expect(result.message).toBe(testCase.expectedMessage)
      }
    })

    it('处理超时错误', async () => {
      const mockError = {
        message: 'timeout',
        response: undefined,
      }

      const result = await responseInterceptorRejected(mockError).catch(e => e)

      expect(result.code).toBe('TIMEOUT')
      expect(result.message).toBe('请求超时，请稍后再试')
    })

    it('处理 ECONNABORTED 超时错误', async () => {
      const mockError = {
        code: 'ECONNABORTED',
        message: 'Request aborted',
        response: undefined,
      }

      const result = await responseInterceptorRejected(mockError).catch(e => e)

      expect(result.code).toBe('TIMEOUT')
      expect(result.message).toBe('请求超时，请稍后再试')
    })

    it('处理网络错误', async () => {
      const mockError = {
        message: 'Network Error',
        response: undefined,
      }

      const result = await responseInterceptorRejected(mockError).catch(e => e)

      expect(result.code).toBe('NETWORK_ERROR')
      expect(result.message).toBe('网络连接失败，请检查网络')
    })

    it('处理未知错误', async () => {
      const mockError = {
        message: 'Something went wrong',
        response: undefined,
      }

      const result = await responseInterceptorRejected(mockError).catch(e => e)

      expect(result.code).toBe('UNKNOWN_ERROR')
      expect(result.message).toBe('Something went wrong')
    })
  })

  describe('全局错误处理', () => {
    it('不显示 VALIDATION_ERROR 的 toast', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            error: { code: 'VALIDATION_ERROR', message: '验证失败' },
          },
        },
      }

      vi.mocked(toastError).mockClear()

      await expect(responseInterceptorRejected(mockError)).rejects.toBeDefined()

      expect(toastError).not.toHaveBeenCalled()
    })

    it('显示其他错误的 toast', async () => {
      const mockError = {
        response: {
          status: 500,
          data: {
            error: { code: 'SERVER_ERROR', message: '服务器错误' },
          },
        },
      }

      vi.mocked(toastError).mockClear()

      await expect(responseInterceptorRejected(mockError)).rejects.toBeDefined()

      expect(toastError).toHaveBeenCalled()
    })
  })

  describe('HTTP 方法', () => {
    describe('GET 方法', () => {
      it('发送 GET 请求并返回数据', async () => {
        const mockResponse = { data: { id: 1, name: 'Test' } }
        mockInstance.get.mockResolvedValue(mockResponse)

        const result = await httpClient.get('/test')

        expect(mockInstance.get).toHaveBeenCalledWith('/test', undefined)
        expect(result).toEqual(mockResponse.data)
      })

      it('GET 带缓存时先检查缓存', async () => {
        const cachedData = { id: 1, name: 'Cached' }
        vi.mocked(apiCache.get).mockReturnValue(cachedData)

        const result = await httpClient.get('/test', { cache: true })

        expect(apiCache.get).toHaveBeenCalled()
        expect(mockInstance.get).not.toHaveBeenCalled()
        expect(result).toEqual(cachedData)
      })

      it('GET 带缓存但缓存不存在时请求并缓存', async () => {
        vi.mocked(apiCache.get).mockReturnValue(null)
        const mockResponse = { data: { id: 1, name: 'Fresh' } }
        mockInstance.get.mockResolvedValue(mockResponse)

        const result = await httpClient.get('/test', { cache: true })

        expect(apiCache.get).toHaveBeenCalled()
        expect(mockInstance.get).toHaveBeenCalled()
        expect(apiCache.set).toHaveBeenCalled()
        expect(result).toEqual(mockResponse.data)
      })
    })

    describe('POST 方法', () => {
      it('发送 POST 请求并返回数据', async () => {
        const testData = { name: 'Test Post' }
        const mockResponse = { data: { id: 1, ...testData } }
        mockInstance.post.mockResolvedValue(mockResponse)

        const result = await httpClient.post('/test', testData)

        expect(mockInstance.post).toHaveBeenCalledWith('/test', testData, undefined)
        expect(result).toEqual(mockResponse.data)
      })
    })

    describe('PUT 方法', () => {
      it('发送 PUT 请求并返回数据', async () => {
        const testData = { id: 1, name: 'Updated' }
        const mockResponse = { data: testData }
        mockInstance.put.mockResolvedValue(mockResponse)

        const result = await httpClient.put('/test/1', testData)

        expect(mockInstance.put).toHaveBeenCalledWith('/test/1', testData, undefined)
        expect(result).toEqual(mockResponse.data)
      })
    })

    describe('DELETE 方法', () => {
      it('发送 DELETE 请求并返回数据', async () => {
        const mockResponse = { data: { success: true } }
        mockInstance.delete.mockResolvedValue(mockResponse)

        const result = await httpClient.delete('/test/1')

        expect(mockInstance.delete).toHaveBeenCalledWith('/test/1', undefined)
        expect(result).toEqual(mockResponse.data)
      })
    })
  })
})
