import { apiRequest } from './client'
import type { AuthTokens, User } from '../types/api'

export function register(email: string, password: string, displayName: string): Promise<AuthTokens> {
  return apiRequest<AuthTokens>('/auth/register', {
    method: 'POST',
    body: {
      email,
      password,
      display_name: displayName,
    },
  })
}

export function login(email: string, password: string): Promise<AuthTokens> {
  return apiRequest<AuthTokens>('/auth/login', {
    method: 'POST',
    body: { email, password },
  })
}

export function refresh(refreshToken: string): Promise<AuthTokens> {
  return apiRequest<AuthTokens>('/auth/refresh', {
    method: 'POST',
    body: { refresh_token: refreshToken },
  })
}

export function getMe(token: string): Promise<User> {
  return apiRequest<User>('/users/me', { token })
}
