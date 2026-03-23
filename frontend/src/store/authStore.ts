import type { User } from '../shared/types/api'

const ACCESS_TOKEN_KEY = 'arb_access_token'
const REFRESH_TOKEN_KEY = 'arb_refresh_token'
const USER_KEY = 'arb_user'

type PersistedAuth = {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
}

function readJson<T>(key: string): T | null {
  const value = localStorage.getItem(key)
  if (!value) {
    return null
  }
  try {
    return JSON.parse(value) as T
  } catch {
    return null
  }
}

export function getAuthState(): PersistedAuth {
  return {
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
    user: readJson<User>(USER_KEY),
  }
}

export function setAuthState(params: PersistedAuth): void {
  if (params.accessToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, params.accessToken)
  } else {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
  }

  if (params.refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, params.refreshToken)
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  if (params.user) {
    localStorage.setItem(USER_KEY, JSON.stringify(params.user))
  } else {
    localStorage.removeItem(USER_KEY)
  }
}

export function clearAuthState(): void {
  setAuthState({
    accessToken: null,
    refreshToken: null,
    user: null,
  })
}
