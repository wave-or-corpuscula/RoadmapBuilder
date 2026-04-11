import { useEffect, useState } from 'react'
import type { SubmitEventHandler } from 'react'

import { getImportPrompt, getImportTemplate } from '../shared/api/planApi'
import type { ImportPlanPayload } from '../shared/types/api'

type Props = {
  onBack: () => void
  onImportPlan: (payload: ImportPlanPayload) => Promise<void>
}

export default function PlanBuilderPage({ onBack, onImportPlan }: Props) {
  const [rawJson, setRawJson] = useState('')
  const [jsonPlaceholder, setJsonPlaceholder] = useState(
    '{\n  "schema_version": "1.0",\n  "title": "Python Backend Roadmap",\n  "skills": [...],\n  "target_skill_ids": [...],\n  "mode": "balanced"\n}',
  )
  const [topic, setTopic] = useState('')
  const [isPromptLoading, setIsPromptLoading] = useState(false)
  const [promptError, setPromptError] = useState<string | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [isJsonInfoOpen, setIsJsonInfoOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    async function loadTemplate() {
      try {
        const template = await getImportTemplate()
        setJsonPlaceholder(JSON.stringify(template, null, 2))
      } catch {
        // Keep fallback placeholder if template endpoint is unavailable.
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
      setToastMessage(null)
      return
    }

    setIsPromptLoading(true)
    setPromptError(null)
    setToastMessage(null)
    try {
      const response = await getImportPrompt(normalizedTopic)
      await navigator.clipboard.writeText(response.prompt)
      setToastMessage('Запрос скопирован в буфер обмена.')
      window.setTimeout(() => setToastMessage(null), 2200)
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : 'Не удалось получить запрос'
      setPromptError(message)
    } finally {
      setIsPromptLoading(false)
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
    <main className="import-page">
      <section className="import-hero">
        <header className="topbar">
          <div>
            <h1>Импорт учебного плана</h1>
            <p>Сгенерируй JSON через ИИ, вставь его сюда и начни работать с графом.</p>
          </div>
          <button className="secondary" onClick={onBack}>
            Back to dashboard
          </button>
        </header>

        <div className="import-grid">
          <div className="import-stack">
            <section className="import-card">
              <h2>Шаг 1. Получить запрос для ИИ</h2>
              <div className="form">
                <label>
                  Тема плана
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
              </div>
            </section>
            <section className="import-hint">
              <h3>Что дальше</h3>
              <ul>
                <li>1. Введи тему и нажми «Получить запрос» — он сразу скопируется.</li>
                <li>2. Вставь этот запрос в ИИ.</li>
                <li>3. Вставь JSON сюда (или загрузи файл) и нажми «Import plan».</li>
              </ul>
            </section>
          </div>

          <section className="import-card">
            <h2>Шаг 2. Вставить JSON-план</h2>
            <form className="form" onSubmit={handleSubmit}>
              <label>
                <span className="label-inline">
                  Plan JSON
                  <button
                    type="button"
                    className="info-icon"
                    onClick={() => setIsJsonInfoOpen(true)}
                    aria-label="Показать формат JSON"
                    title="Показать формат JSON"
                  >
                    i
                  </button>
                </span>
                <textarea
                  rows={22}
                  className="plan-json-input"
                  value={rawJson}
                  onChange={(event) => setRawJson(event.target.value)}
                  spellCheck={false}
                />
              </label>
              <label>
                Или выбрать JSON-файл
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
        </div>
      </section>
      {toastMessage ? (
        <div className="toast" role="status" aria-live="polite">
          {toastMessage}
        </div>
      ) : null}
      {isJsonInfoOpen ? (
        <div className="modal-backdrop" onClick={() => setIsJsonInfoOpen(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <header className="modal-head">
              <h3>Формат JSON</h3>
              <button type="button" className="secondary" onClick={() => setIsJsonInfoOpen(false)}>
                Close
              </button>
            </header>
            <pre className="json-preview">{jsonPlaceholder}</pre>
          </div>
        </div>
      ) : null}
    </main>
  )
}
