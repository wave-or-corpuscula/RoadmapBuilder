const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  token?: string | null
  body?: unknown
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })

  if (!response.ok) {
    const text = await response.text()
    let message = text
    try {
      const parsed = JSON.parse(text) as { detail?: string }
      if (parsed.detail) {
        message = parsed.detail
      }
    } catch {
      // keep raw text
    }
    throw new ApiError(message || `HTTP ${response.status}`, response.status)
  }

  if (response.status === 204) {
    return null as T
  }

  return (await response.json()) as T
}
