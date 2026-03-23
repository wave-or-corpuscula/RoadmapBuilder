import { useEffect, useMemo, useState } from 'react'

import './App.css'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PlanBuilderPage from './pages/PlanBuilderPage'
import { getMe, login, refresh, register } from './shared/api/authApi'
import { createPlan, getProgress } from './shared/api/planApi'
import { ApiError } from './shared/api/client'
import { clearAuthState, getAuthState, setAuthState } from './store/authStore'
import type { LearningMode, Plan, Progress, User } from './shared/types/api'

type AppPath = '/dashboard' | '/plans/new'

function getCurrentPath(): AppPath {
  const path = window.location.pathname
  if (path === '/plans/new') {
    return '/plans/new'
  }
  return '/dashboard'
}

function App() {
  const [path, setPath] = useState<AppPath>(getCurrentPath())
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [refreshToken, setRefreshToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [progress, setProgress] = useState<Progress | null>(null)
  const isAuthenticated = useMemo(() => Boolean(accessToken && user), [accessToken, user])

  function navigate(nextPath: AppPath) {
    window.history.pushState({}, '', nextPath)
    setPath(nextPath)
  }

  useEffect(() => {
    const onPopState = () => setPath(getCurrentPath())
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  async function bootstrap() {
    const persisted = getAuthState()
    if (!persisted.accessToken || !persisted.refreshToken || !persisted.user) {
      return
    }

    try {
      const me = await getMe(persisted.accessToken)
      setAccessToken(persisted.accessToken)
      setRefreshToken(persisted.refreshToken)
      setUser(me)
      const currentProgress = await getProgress(persisted.accessToken)
      setProgress(currentProgress)
      setAuthState({ accessToken: persisted.accessToken, refreshToken: persisted.refreshToken, user: me })
      return
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) {
        clearAuthState()
        return
      }
    }

    try {
      const tokens = await refresh(persisted.refreshToken)
      const me = await getMe(tokens.access_token)
      setAccessToken(tokens.access_token)
      setRefreshToken(tokens.refresh_token)
      setUser(me)
      const currentProgress = await getProgress(tokens.access_token)
      setProgress(currentProgress)
      setAuthState({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token, user: me })
    } catch {
      clearAuthState()
    }
  }

  useEffect(() => {
    void bootstrap()
  }, [])

  async function handleLogin(email: string, password: string) {
    const tokens = await login(email, password)
    const me = await getMe(tokens.access_token)
    setAccessToken(tokens.access_token)
    setRefreshToken(tokens.refresh_token)
    setUser(me)
    const currentProgress = await getProgress(tokens.access_token)
    setProgress(currentProgress)
    setAuthState({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token, user: me })
    navigate('/dashboard')
  }

  async function handleRegister(email: string, password: string, displayName: string) {
    const tokens = await register(email, password, displayName)
    const me = await getMe(tokens.access_token)
    setAccessToken(tokens.access_token)
    setRefreshToken(tokens.refresh_token)
    setUser(me)
    const currentProgress = await getProgress(tokens.access_token)
    setProgress(currentProgress)
    setAuthState({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token, user: me })
    navigate('/dashboard')
  }

  async function refreshProgress() {
    if (!accessToken) {
      return
    }
    const currentProgress = await getProgress(accessToken)
    setProgress(currentProgress)
  }

  async function handleCreatePlan(targetSkillIds: string[], mode: LearningMode): Promise<Plan> {
    if (!accessToken) {
      throw new Error('Not authenticated')
    }
    const created = await createPlan(accessToken, targetSkillIds, mode)
    const currentProgress = await getProgress(accessToken)
    setProgress(currentProgress)
    return created
  }

  function handleSignOut() {
    clearAuthState()
    setAccessToken(null)
    setRefreshToken(null)
    setUser(null)
    setProgress(null)
    navigate('/dashboard')
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} onRegister={handleRegister} />
  }

  if (!refreshToken) {
    return <LoginPage onLogin={handleLogin} onRegister={handleRegister} />
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} onRegister={handleRegister} />
  }

  if (path === '/plans/new') {
    return <PlanBuilderPage onBack={() => navigate('/dashboard')} onCreatePlan={handleCreatePlan} />
  }

  return (
    <DashboardPage
      user={user}
      progress={progress}
      onOpenBuilder={() => navigate('/plans/new')}
      onSignOut={handleSignOut}
      onRefreshProgress={refreshProgress}
    />
  )
}

export default App
