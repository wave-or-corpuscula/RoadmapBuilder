import { useState } from 'react'
import type { SubmitEventHandler } from 'react'

import type { LearningMode, Plan } from '../shared/types/api'

type Props = {
  onBack: () => void
  onCreatePlan: (targetSkillIds: string[], mode: LearningMode) => Promise<Plan>
}

export default function PlanBuilderPage({ onBack, onCreatePlan }: Props) {
  const [targetsRaw, setTargetsRaw] = useState('goal')
  const [mode, setMode] = useState<LearningMode>('balanced')
  const [createdPlan, setCreatedPlan] = useState<Plan | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (event) => {
    event.preventDefault()
    setError(null)
    setCreatedPlan(null)

    const targetSkillIds = targetsRaw
      .split(',')
      .map((value) => value.trim())
      .filter((value) => value.length > 0)

    if (targetSkillIds.length === 0) {
      setError('Provide at least one target skill id.')
      return
    }

    setIsLoading(true)
    try {
      const plan = await onCreatePlan(targetSkillIds, mode)
      setCreatedPlan(plan)
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Failed to create plan'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Plan Builder</h1>
          <p>Create a personalized learning plan from backend graph.</p>
        </div>
        <button className="secondary" onClick={onBack}>
          Back to dashboard
        </button>
      </header>

      <section className="card">
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Target skill IDs (comma separated)
            <input
              value={targetsRaw}
              onChange={(event) => setTargetsRaw(event.target.value)}
              placeholder="goal, another_goal"
            />
          </label>
          <label>
            Learning mode
            <select value={mode} onChange={(event) => setMode(event.target.value as LearningMode)}>
              <option value="surface">surface</option>
              <option value="balanced">balanced</option>
              <option value="deep">deep</option>
            </select>
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Building...' : 'Create plan'}
          </button>
        </form>
      </section>

      {createdPlan ? (
        <section className="card">
          <h2>Created plan</h2>
          <p>Plan ID: {createdPlan.id}</p>
          <ul className="plain-list">
            {createdPlan.ordered_skill_ids.map((skillId) => (
              <li key={skillId}>
                <span>{skillId}</span>
                <strong>{createdPlan.skill_statuses[skillId]}</strong>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  )
}
