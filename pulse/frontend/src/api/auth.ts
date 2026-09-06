import { api } from './client'

export interface LoginRequest { email: string; password: string }
export interface RegisterRequest { email: string; password: string; name?: string }
export interface TokenResponse { access_token: string; token_type: string }
export interface User { id: number; email: string; name?: string }

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<TokenResponse>('/api/auth/login', data).then(r => r.data),

  register: (data: RegisterRequest) =>
    api.post<TokenResponse>('/api/auth/register', data).then(r => r.data),

  me: () =>
    api.get<User>('/api/auth/me').then(r => r.data),
}
