import type { Progress, User } from '../shared/types/api'

type Props = {
  user: User
  progress: Progress | null
  onOpenImport: () => void
  onSignOut: () => void
  onRefreshProgress: () => Promise<void>
}

export default function DashboardPage({
  user,
  progress,
  onOpenImport,
  onSignOut,
  onRefreshProgress,
}: Props) {
  const statuses = progress?.statuses ?? {}
  const entries = Object.entries(statuses).sort(([left], [right]) => left.localeCompare(right))

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Dashboard</h1>
          <p>
            {user.display_name} · {user.email}
          </p>
        </div>
        <div className="actions">
          <button className="secondary" onClick={onRefreshProgress}>
            Refresh progress
          </button>
          <button className="secondary" onClick={onOpenImport}>
            Import plan JSON
          </button>
          <button className="danger" onClick={onSignOut}>
            Sign out
          </button>
        </div>
      </header>

      <section className="card">
        <h2>Progress</h2>
        {entries.length === 0 ? (
          <p>No progress yet.</p>
        ) : (
          <ul className="plain-list">
            {entries.map(([skillId, status]) => (
              <li key={skillId}>
                <span>{skillId}</span>
                <strong>{status}</strong>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
