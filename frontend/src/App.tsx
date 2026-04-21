import { useEffect, useMemo, useState } from 'react'

import './App.css'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PlanBuilderPage from './pages/PlanBuilderPage'
import PlanWorkspacePage from './pages/PlanWorkspacePage'
import { getMe, login, refresh, register } from './shared/api/authApi'
import {
  deletePlan,
  derivePlan,
  getPlan,
  getPlanGraph,
  getProgress,
  importPlan,
  listPlans,
  updatePlanSkillNote,
  updatePlanSkillStatus,
  updatePlanTitle,
} from './shared/api/planApi'
import { ApiError } from './shared/api/client'
import { clearAuthState, getAuthState, setAuthState } from './store/authStore'
import type { ImportPlanPayload, KnowledgeStatus, Plan, PlanGraph, Progress, User } from './shared/types/api'

type AppPath = '/dashboard' | '/plans/new' | '/plans/view'
const LAST_PLAN_ID_KEY = 'arb:last_plan_id'

function getCurrentPath(): AppPath {
  const path = window.location.pathname
  if (path === '/plans/new') {
    return '/plans/new'
  }
  if (path === '/plans/view') {
    return '/plans/view'
  }
  return '/dashboard'
}

function App() {
  const [path, setPath] = useState<AppPath>(getCurrentPath())
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [refreshToken, setRefreshToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [progress, setProgress] = useState<Progress | null>(null)
  const [recentPlans, setRecentPlans] = useState<Plan[]>([])
  const [currentPlan, setCurrentPlan] = useState<Plan | null>(null)
  const [currentGraph, setCurrentGraph] = useState<PlanGraph | null>(null)
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

  function saveLastPlanId(planId: string) {
    localStorage.setItem(LAST_PLAN_ID_KEY, planId)
  }

  function getLastPlanId(): string | null {
    return localStorage.getItem(LAST_PLAN_ID_KEY)
  }

  function clearLastPlanId() {
    localStorage.removeItem(LAST_PLAN_ID_KEY)
  }

  async function refreshRecentPlans(token: string) {
    const plans = await listPlans(token)
    setRecentPlans(plans)
  }

  async function openExistingPlan(token: string, planId: string) {
    const [plan, graph] = await Promise.all([getPlan(token, planId), getPlanGraph(token, planId)])
    setCurrentPlan(plan)
    setCurrentGraph(graph)
    saveLastPlanId(plan.id)
  }

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
      try {
        await refreshRecentPlans(persisted.accessToken)
      } catch {
        setRecentPlans([])
      }
      const lastPlanId = getLastPlanId()
      if (lastPlanId) {
        try {
          await openExistingPlan(persisted.accessToken, lastPlanId)
        } catch {
          clearLastPlanId()
        }
      }
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
      try {
        await refreshRecentPlans(tokens.access_token)
      } catch {
        setRecentPlans([])
      }
      const lastPlanId = getLastPlanId()
      if (lastPlanId) {
        try {
          await openExistingPlan(tokens.access_token, lastPlanId)
        } catch {
          clearLastPlanId()
        }
      }
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
    try {
      await refreshRecentPlans(tokens.access_token)
    } catch {
      setRecentPlans([])
    }
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
    try {
      await refreshRecentPlans(tokens.access_token)
    } catch {
      setRecentPlans([])
    }
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

  async function handleImportPlan(payload: ImportPlanPayload): Promise<void> {
    if (!accessToken) {
      throw new Error('Not authenticated')
    }
    const created = await importPlan(accessToken, payload)
    const graph = await getPlanGraph(accessToken, created.id)
    const currentProgress = await getProgress(accessToken)
    setProgress(currentProgress)
    setCurrentPlan(created)
    setCurrentGraph(graph)
    saveLastPlanId(created.id)
    try {
      await refreshRecentPlans(accessToken)
    } catch {
      setRecentPlans([])
    }
    navigate('/plans/view')
  }

  async function handleUpdatePlanSkillStatus(planId: string, skillId: string, status: KnowledgeStatus): Promise<Plan> {
    if (!accessToken) {
      throw new Error('Not authenticated')
    }
    const updatedPlan = await updatePlanSkillStatus(accessToken, planId, skillId, status)
    const currentProgress = await getProgress(accessToken)
    setProgress(currentProgress)
    if (currentPlan && currentPlan.id === updatedPlan.id) {
      setCurrentPlan(updatedPlan)
    }
    return updatedPlan
  }

  async function handleOpenPlan(planId: string) {
    if (!accessToken) {
      throw new Error('Not authenticated')
    }
    await openExistingPlan(accessToken, planId)
    navigate('/plans/view')
  }

  async function handleUpdatePlanSkillNote(planId: string, skillId: string, note: string): Promise<Plan> {
    if (!accessToken) {
      throw new Error('Not authenticated')
    }
    const updatedPlan = await updatePlanSkillNote(accessToken, planId, skillId, note)
    if (currentPlan && currentPlan.id === updatedPlan.id) {
      setCurrentPlan(updatedPlan)
    }
    return updatedPlan
  }

  async function handleUpdatePlanTitle(planId: string, title: string): Promise<Plan> {
    if (!accessToken) {
      throw new Error('Not authenticated')
    }
    const updatedPlan = await updatePlanTitle(accessToken, planId, title)
    if (currentPlan && currentPlan.id === updatedPlan.id) {
      setCurrentPlan(updatedPlan)
    }
    setRecentPlans((prev) => prev.map((plan) => (plan.id === updatedPlan.id ? updatedPlan : plan)))
    return updatedPlan
  }

  async function handleCreateDerivedPlan(planId: string, skillId: string): Promise<Plan> {
    if (!accessToken) {
      throw new Error('Not authenticated')
    }
    const derived = await derivePlan(accessToken, planId, skillId)
    const graph = await getPlanGraph(accessToken, derived.id)
    setCurrentPlan(derived)
    setCurrentGraph(graph)
    saveLastPlanId(derived.id)
    try {
      await refreshRecentPlans(accessToken)
    } catch {
      setRecentPlans([])
    }
    navigate('/plans/view')
    return derived
  }

  async function handleDeletePlan(planId: string, fallbackPlanId: string | null): Promise<void> {
    if (!accessToken) {
      throw new Error('Not authenticated')
    }

    const result = await deletePlan(accessToken, planId)
    const deleted = new Set(result.deleted_ids)
    const plansAfterDelete = (await listPlans(accessToken)).sort(
      (left, right) => right.created_at.localeCompare(left.created_at),
    )
    setRecentPlans(plansAfterDelete)

    if (currentPlan && deleted.has(currentPlan.id)) {
      clearLastPlanId()
      const preferred =
        fallbackPlanId && !deleted.has(fallbackPlanId)
          ? plansAfterDelete.find((item) => item.id === fallbackPlanId)
          : null
      const nextPlan = preferred ?? plansAfterDelete[0] ?? null
      if (nextPlan) {
        await openExistingPlan(accessToken, nextPlan.id)
        navigate('/plans/view')
      } else {
        setCurrentPlan(null)
        setCurrentGraph(null)
        navigate('/dashboard')
      }
    }
  }

  function handleSignOut() {
    clearAuthState()
    setAccessToken(null)
    setRefreshToken(null)
    setUser(null)
    setProgress(null)
    setRecentPlans([])
    setCurrentPlan(null)
    setCurrentGraph(null)
    clearLastPlanId()
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
    return (
      <PlanBuilderPage
        onBack={() => navigate('/dashboard')}
        onImportPlan={handleImportPlan}
      />
    )
  }

  if (path === '/plans/view') {
    if (!currentPlan || !currentGraph) {
      return (
        <main className="app-shell">
          <header className="topbar">
            <h1>План</h1>
          </header>
          <section className="card">
            <p>План не выбран.</p>
            <button onClick={() => navigate('/dashboard')}>Назад на дашборд</button>
          </section>
        </main>
      )
    }

    return (
      <PlanWorkspacePage
        plan={currentPlan}
        graph={currentGraph}
        plans={recentPlans}
        onBack={() => navigate('/dashboard')}
        onOpenPlan={handleOpenPlan}
        onDeletePlan={handleDeletePlan}
        onCreateDerivedPlan={handleCreateDerivedPlan}
        onUpdatePlanTitle={handleUpdatePlanTitle}
        onUpdatePlanSkillStatus={handleUpdatePlanSkillStatus}
        onUpdatePlanSkillNote={handleUpdatePlanSkillNote}
      />
    )
  }

  return (
    <DashboardPage
      user={user}
      progress={progress}
      recentPlans={recentPlans}
      currentGraph={currentGraph}
      onOpenImport={() => navigate('/plans/new')}
      onOpenPlan={handleOpenPlan}
      onSignOut={handleSignOut}
      onRefreshProgress={refreshProgress}
    />
  )
}

export default App
