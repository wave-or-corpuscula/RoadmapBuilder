import { useEffect, useState } from 'react'
import type { SubmitEventHandler } from 'react'

import { getImportPrompt, getImportTemplate } from '../shared/api/planApi'
import type { ImportPlanPayload } from '../shared/types/api'

type Props = {
  onBack: () => void
  onImportPlan: (payload: ImportPlanPayload) => Promise<void>
}

export default function PlanBuilderPage({ onBack, onImportPlan }: Props) {
  const [rawJson, setRawJson] = useState(
    '{\n  "schema_version": "1.0",\n  "skills": [],\n  "target_skill_ids": [],\n  "mode": "balanced"\n}',
  )
  const [topic, setTopic] = useState('')
  const [generatedPrompt, setGeneratedPrompt] = useState('')
  const [isPromptLoading, setIsPromptLoading] = useState(false)
  const [promptError, setPromptError] = useState<string | null>(null)
  const [copyMessage, setCopyMessage] = useState<string | null>(null)
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

  async function handleGeneratePrompt() {
    const normalizedTopic = topic.trim()
    if (!normalizedTopic) {
      setPromptError('Введите тему для плана.')
      setGeneratedPrompt('')
      setCopyMessage(null)
      return
    }

    setIsPromptLoading(true)
    setPromptError(null)
    setCopyMessage(null)
    try {
      const response = await getImportPrompt(normalizedTopic)
      setGeneratedPrompt(response.prompt)
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Failed to build prompt'
      setPromptError(message)
      setGeneratedPrompt('')
    } finally {
      setIsPromptLoading(false)
    }
  }

  async function handleCopyPrompt() {
    if (!generatedPrompt.trim()) {
      setCopyMessage('Сначала сгенерируйте запрос.')
      return
    }

    try {
      await navigator.clipboard.writeText(generatedPrompt)
      setCopyMessage('Запрос скопирован.')
    } catch {
      setCopyMessage('Не удалось скопировать запрос.')
    }
  }

  const handleSubmit: SubmitEventHandler<HTMLFormElement> = async (event) => {
    event.preventDefault()
    setError(null)

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
    if (!payload.title && topic.trim()) {
      payload.title = topic.trim()
    }

    setIsLoading(true)
    try {
      await onImportPlan(payload)
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Failed to import plan'
      setError(message)
    } finally {
      setIsLoading(false)
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
        <div className="form prompt-builder">
          <label>
            Тема для генерации плана
            <input
              type="text"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Например: Backend на Python для junior+"
            />
          </label>
          <button type="button" onClick={handleGeneratePrompt} disabled={isPromptLoading}>
            {isPromptLoading ? 'Генерируем...' : 'Получить запрос'}
          </button>
          {promptError ? <p className="error-text">{promptError}</p> : null}
          <label>
            Запрос для ИИ
            <textarea rows={12} value={generatedPrompt} readOnly spellCheck={false} />
          </label>
          <div className="actions">
            <button type="button" className="secondary" onClick={handleCopyPrompt} disabled={!generatedPrompt.trim()}>
              Скопировать запрос
            </button>
            {copyMessage ? <p className="status-text">{copyMessage}</p> : null}
          </div>
        </div>

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
    </main>
  )
}
