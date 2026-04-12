import { useEffect, useMemo, useRef, useState } from 'react'

import PlanGraphView from '../components/PlanGraphView'
import type { KnowledgeStatus, Plan, PlanGraph } from '../shared/types/api'

type Props = {
  plan: Plan
  graph: PlanGraph
  onBack: () => void
  onUpdatePlanTitle: (planId: string, title: string) => Promise<Plan>
  onUpdatePlanSkillStatus: (planId: string, skillId: string, status: KnowledgeStatus) => Promise<Plan>
  onUpdatePlanSkillNote: (planId: string, skillId: string, note: string) => Promise<Plan>
}

function escapeHtml(raw: string): string {
  return raw
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
}

function renderMarkdownPreview(markdown: string): string {
  let html = escapeHtml(markdown)
  html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  html = html.replace(/`(.+?)`/g, '<code>$1</code>')
  html = html.replace(/^- (.*)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
  html = html.replace(/\n/g, '<br />')
  return html
}

export default function PlanWorkspacePage({
  plan,
  graph,
  onBack,
  onUpdatePlanTitle,
  onUpdatePlanSkillStatus,
  onUpdatePlanSkillNote,
}: Props) {
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null)
  const [noteDraft, setNoteDraft] = useState('')
  const [titleDraft, setTitleDraft] = useState(plan.title)
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [isSavingTitle, setIsSavingTitle] = useState(false)
  const [titleError, setTitleError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [isSavingNote, setIsSavingNote] = useState(false)
  const titleInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    setTitleDraft(plan.title)
    setIsEditingTitle(false)
    setIsSavingTitle(false)
    setTitleError(null)
  }, [plan.title])

  useEffect(() => {
    if (!selectedSkillId) {
      setNoteDraft('')
      return
    }
    setNoteDraft(plan.skill_notes[selectedSkillId] ?? '')
  }, [plan.skill_notes, selectedSkillId])

  const selectedSkill = useMemo(
    () => graph.skills.find((item) => item.id === selectedSkillId) ?? null,
    [graph.skills, selectedSkillId],
  )

  async function handleStatusChange(status: KnowledgeStatus) {
    if (!selectedSkillId) {
      return
    }
    try {
      await onUpdatePlanSkillStatus(plan.id, selectedSkillId, status)
      setSaveError(null)
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to update status')
    }
  }

  async function persistNote(skillId: string, note: string) {
    const stored = plan.skill_notes[skillId] ?? ''
    if (stored === note) {
      return
    }

    try {
      setIsSavingNote(true)
      await onUpdatePlanSkillNote(plan.id, skillId, note)
      setSaveError(null)
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save note')
    } finally {
      setIsSavingNote(false)
    }
  }

  async function flushCurrentNote() {
    if (!selectedSkillId) {
      return
    }
    await persistNote(selectedSkillId, noteDraft)
  }

  function handleSelectSkill(nextSkillId: string | null) {
    const currentSkill = selectedSkillId
    const currentDraft = noteDraft
    void (async () => {
      if (currentSkill) {
        await persistNote(currentSkill, currentDraft)
      }
      setSelectedSkillId(nextSkillId)
      setSaveError(null)
    })()
  }

  async function handleSaveTitle() {
    const normalized = titleDraft.trim()
    if (!normalized) {
      setTitleError('Введите название плана')
      return
    }
    if (normalized === plan.title) {
      setIsEditingTitle(false)
      setTitleError(null)
      return
    }
    try {
      setIsSavingTitle(true)
      await onUpdatePlanTitle(plan.id, normalized)
      setIsEditingTitle(false)
      setTitleError(null)
    } catch (error) {
      setTitleError(error instanceof Error ? error.message : 'Не удалось обновить название плана')
    } finally {
      setIsSavingTitle(false)
    }
  }

  function enableTitleEditing() {
    if (isSavingTitle) {
      return
    }
    if (!isEditingTitle) {
      setIsEditingTitle(true)
      requestAnimationFrame(() => titleInputRef.current?.select())
    }
  }

  async function handleTitleBlur() {
    if (!isEditingTitle) {
      return
    }
    await handleSaveTitle()
    setIsEditingTitle(false)
  }

  async function handleBack() {
    await flushCurrentNote()
    onBack()
  }

  return (
    <main className="plan-workspace">
      <header className="workspace-topbar">
        <div>
          <div className="workspace-title-row">
            <input
              ref={titleInputRef}
              className={`workspace-title-input ${isEditingTitle ? 'editing' : ''}`}
              value={titleDraft}
              onChange={(event) => setTitleDraft(event.target.value)}
              onClick={enableTitleEditing}
              onFocus={enableTitleEditing}
              onBlur={() => void handleTitleBlur()}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                  event.currentTarget.blur()
                  return
                }
                if (event.key === 'Escape') {
                  setTitleDraft(plan.title)
                  setTitleError(null)
                  setIsEditingTitle(false)
                  event.currentTarget.blur()
                }
              }}
              placeholder="Название плана"
              maxLength={120}
              readOnly={!isEditingTitle || isSavingTitle}
              aria-label="Название плана"
            />
          </div>
          <p>Основной режим работы с планом.</p>
          {isSavingTitle ? <p className="status-text">Сохраняю название...</p> : null}
          {titleError ? <p className="error-text">{titleError}</p> : null}
        </div>
        <button className="secondary" onClick={() => void handleBack()}>
          Назад к дашборду
        </button>
      </header>
      <div className={`workspace-body ${selectedSkill ? 'with-panel' : ''}`}>
        <section className="workspace-main">
          <PlanGraphView
            graph={graph}
            plan={plan}
            selectedSkillId={selectedSkillId}
            onSelectSkill={handleSelectSkill}
          />
        </section>
        {selectedSkill ? (
          <aside className="workspace-sidebar">
            <section className="card">
              <h2>{selectedSkill.title}</h2>
              <p>{selectedSkill.description}</p>
              <label>
                Knowledge status
                <select
                  value={plan.skill_statuses[selectedSkill.id] ?? 'unknown'}
                  onChange={(event) => void handleStatusChange(event.target.value as KnowledgeStatus)}
                >
                  <option value="unknown">unknown</option>
                  <option value="learning">learning</option>
                  <option value="mastered">mastered</option>
                </select>
              </label>
              <label>
                Notes
                <textarea
                  rows={9}
                  value={noteDraft}
                  onChange={(event) => setNoteDraft(event.target.value)}
                  placeholder="Markdown notes..."
                />
              </label>
              <div className="markdown-preview" dangerouslySetInnerHTML={{ __html: renderMarkdownPreview(noteDraft) }} />
              {isSavingNote ? <p className="status-text">Saving...</p> : null}
              {saveError ? <p className="error-text">{saveError}</p> : null}
            </section>
          </aside>
        ) : null}
      </div>
    </main>
  )
}
