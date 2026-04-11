import type { KnowledgeStatus, Plan, PlanGraph, Progress, User } from '../shared/types/api'
import { useMemo, useState } from 'react'

type Props = {
  user: User
  progress: Progress | null
  recentPlans: Plan[]
  currentGraph: PlanGraph | null
  onOpenImport: () => void
  onOpenPlan: (planId: string) => Promise<void>
  onSignOut: () => void
  onRefreshProgress: () => Promise<void>
}

export default function DashboardPage({
  user,
  progress,
  recentPlans,
  currentGraph,
  onOpenImport,
  onOpenPlan,
  onSignOut,
  onRefreshProgress,
}: Props) {
  const [statusFilter, setStatusFilter] = useState<'all' | KnowledgeStatus>('all')
  const [sortBy, setSortBy] = useState<'title' | 'status'>('title')
  const titleBySkillId = Object.fromEntries((currentGraph?.skills ?? []).map((skill) => [skill.id, skill.title]))
  const statuses = progress?.statuses ?? {}
  const allEntries = Object.entries(statuses)
    .map(([skillId, status]) => ({
      skillId,
      status,
      title: titleBySkillId[skillId] ?? skillId,
    }))

  const entries = useMemo(() => {
    const filtered = allEntries.filter((item) => (statusFilter === 'all' ? true : item.status === statusFilter))
    if (sortBy === 'status') {
      const rank: Record<KnowledgeStatus, number> = {
        unknown: 1,
        learning: 2,
        mastered: 3,
      }
      return filtered.sort((left, right) => {
        const byStatus = rank[right.status] - rank[left.status]
        if (byStatus !== 0) {
          return byStatus
        }
        return left.title.localeCompare(right.title)
      })
    }
    return filtered.sort((left, right) => left.title.localeCompare(right.title))
  }, [allEntries, sortBy, statusFilter])

  const totals = {
    unknown: allEntries.filter((item) => item.status === 'unknown').length,
    learning: allEntries.filter((item) => item.status === 'learning').length,
    mastered: allEntries.filter((item) => item.status === 'mastered').length,
  }

  function statusLabel(status: KnowledgeStatus): string {
    if (status === 'mastered') {
      return 'Освоен'
    }
    if (status === 'learning') {
      return 'В процессе'
    }
    return 'Не начат'
  }

  function statusLevel(status: KnowledgeStatus): number {
    if (status === 'mastered') {
      return 3
    }
    if (status === 'learning') {
      return 2
    }
    return 1
  }

  function toggleStatusFilter(nextStatus: KnowledgeStatus): void {
    setStatusFilter((prev) => (prev === nextStatus ? 'all' : nextStatus))
  }

  return (
    <main className="dashboard-page">
      <section className="dashboard-hero">
        <header className="topbar">
          <div>
            <h1>Панель управления</h1>
            <p>
              {user.display_name} · {user.email}
            </p>
          </div>
          <div className="actions">
            <button className="secondary" onClick={onRefreshProgress}>
              Обновить прогресс
            </button>
            <button onClick={onOpenImport}>
              Импортировать план
            </button>
            <button className="danger" onClick={onSignOut}>
              Выйти
            </button>
          </div>
        </header>

        <div className="dashboard-grid">
          <section className="dashboard-card">
            <h2>Последние планы</h2>
            {recentPlans.length === 0 ? (
              <p>Пока нет планов. Импортируй первый JSON-план.</p>
            ) : (
              <ul className="plain-list">
                {recentPlans.map((plan) => (
                  <li key={plan.id}>
                    <span>{plan.title}</span>
                    <button className="secondary compact" onClick={() => void onOpenPlan(plan.id)}>
                      Открыть
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="dashboard-card">
            <h2>Прогресс по навыкам</h2>
            <div className="progress-summary">
              <button
                type="button"
                className={`pill-button unknown ${statusFilter === 'unknown' ? 'active' : ''}`}
                onClick={() => toggleStatusFilter('unknown')}
              >
                Не начато: {totals.unknown}
              </button>
              <button
                type="button"
                className={`pill-button learning ${statusFilter === 'learning' ? 'active' : ''}`}
                onClick={() => toggleStatusFilter('learning')}
              >
                В процессе: {totals.learning}
              </button>
              <button
                type="button"
                className={`pill-button mastered ${statusFilter === 'mastered' ? 'active' : ''}`}
                onClick={() => toggleStatusFilter('mastered')}
              >
                Освоено: {totals.mastered}
              </button>
            </div>
            <div className="progress-controls">
              <label>
                Сортировка
                <select value={sortBy} onChange={(event) => setSortBy(event.target.value as 'title' | 'status')}>
                  <option value="title">По названию</option>
                  <option value="status">По уровню</option>
                </select>
              </label>
            </div>
            {entries.length === 0 ? (
              <p>Прогресс пока пуст. Обнови статус навыков в плане.</p>
            ) : (
              <ul className="progress-list">
                {entries.map((item) => {
                  const level = statusLevel(item.status)
                  return (
                    <li key={item.skillId} className="progress-row">
                      <div className="progress-meta">
                        <strong>{item.title}</strong>
                        <span>{item.skillId}</span>
                      </div>
                      <div className="progress-level">
                        <div className={`level-track ${item.status}`} aria-hidden="true">
                          <span className={level >= 1 ? 'active' : ''} />
                          <span className={level >= 2 ? 'active' : ''} />
                          <span className={level >= 3 ? 'active' : ''} />
                        </div>
                        <span className={`status-tag ${item.status}`}>{statusLabel(item.status)}</span>
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </section>
        </div>
      </section>
    </main>
  )
}
