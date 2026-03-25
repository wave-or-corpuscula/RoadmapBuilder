import { useEffect, useState } from 'react'
import type { SubmitEventHandler } from 'react'

import PlanGraphView from '../components/PlanGraphView'
import { getImportTemplate } from '../shared/api/planApi'
import type { ImportPlanPayload, KnowledgeStatus, Plan, PlanGraph } from '../shared/types/api'

type Props = {
  onBack: () => void
  onImportPlan: (payload: ImportPlanPayload) => Promise<{ plan: Plan; graph: PlanGraph }>
  onUpdatePlanSkillStatus: (planId: string, skillId: string, status: KnowledgeStatus) => Promise<Plan>
}

export default function PlanBuilderPage({ onBack, onImportPlan, onUpdatePlanSkillStatus }: Props) {
  const [rawJson, setRawJson] = useState('{\n  "skills": [],\n  "target_skill_ids": [],\n  "mode": "balanced"\n}')
  const [createdPlan, setCreatedPlan] = useState<Plan | null>(null)
  const [graph, setGraph] = useState<PlanGraph | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    async function loadTemplate() {
      try {
        const template = await getImportTemplate()
        setRawJson(JSON.stringify(template, null, 2))
      } catch {
        // Keep fallback starter JSON if template endpoint is unavailable.
      }
    }
    void loadTemplate()
  }, [])

  function validatePayload(payload: ImportPlanPayload): string | null {
    if (!Array.isArray(payload.skills) || payload.skills.length === 0) {
      return 'skills must be a non-empty array.'
    }
    if (!Array.isArray(payload.target_skill_ids) || payload.target_skill_ids.length === 0) {
      return 'target_skill_ids must be a non-empty array.'
    }
    return null
  }

  const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (event) => {
    event.preventDefault()
    setError(null)
    setCreatedPlan(null)
    setGraph(null)

    let payload: ImportPlanPayload
    try {
      payload = JSON.parse(rawJson) as ImportPlanPayload
    } catch {
      setError('JSON is invalid.')
      return
    }

    const validationError = validatePayload(payload)
    if (validationError) {
      setError(validationError)
      return
    }

    setIsLoading(true)
    try {
      const result = await onImportPlan(payload)
      const plan = result.plan
      setCreatedPlan(plan)
      setGraph(result.graph)
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Failed to import plan'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  async function handleStatusChange(skillId: string, status: KnowledgeStatus) {
    if (!createdPlan) {
      return
    }
    try {
      const updatedPlan = await onUpdatePlanSkillStatus(createdPlan.id, skillId, status)
      setCreatedPlan(updatedPlan)
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Failed to update status'
      setError(message)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Plan Import</h1>
          <p>Upload plan JSON, then track progress directly in imported graph.</p>
        </div>
        <button className="secondary" onClick={onBack}>
          Back to dashboard
        </button>
      </header>

      <section className="card">
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Plan JSON
            <textarea
              rows={12}
              value={rawJson}
              onChange={(event) => setRawJson(event.target.value)}
              spellCheck={false}
            />
          </label>
          <label>
            Or pick JSON file
            <input
              type="file"
              accept=".json,application/json"
              onChange={async (event) => {
                const file = event.target.files?.[0]
                if (!file) {
                  return
                }
                const text = await file.text()
                setRawJson(text)
              }}
            />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Importing...' : 'Import plan'}
          </button>
        </form>
      </section>

      {createdPlan && graph ? (
        <section className="card">
          <h2>Imported graph</h2>
          <p>Plan ID: {createdPlan.id}</p>
          <PlanGraphView graph={graph} plan={createdPlan} onStatusChange={handleStatusChange} />
        </section>
      ) : null}
    </main>
  )
}
