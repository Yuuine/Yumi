import { httpClient } from './http-client'

export interface LoginRequest {
  nickname: string
  password: string
}

export interface RegisterRequest {
  nickname: string
  password: string
}

export interface AuthResponse {
  userId: string
  accessToken: string
  refreshToken: string
}

class AuthApi {
  async login(request: LoginRequest): Promise<AuthResponse> {
    return httpClient.post<AuthResponse>('/auth/login', request)
  }

  async register(request: RegisterRequest): Promise<AuthResponse> {
    return httpClient.post<AuthResponse>('/auth/register', request)
  }

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    return httpClient.post<AuthResponse>('/auth/refresh', { refreshToken })
  }

  async getCurrentUser(): Promise<{ userId: string; nickname: string }> {
    return httpClient.get<{ userId: string; nickname: string }>('/auth/me')
  }
}

export const authApi = new AuthApi()
