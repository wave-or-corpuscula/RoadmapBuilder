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

const STATUS_OPTIONS: Array<{ value: KnowledgeStatus; label: string; className: string }> = [
  { value: 'unknown', label: 'Не начато', className: 'unknown' },
  { value: 'learning', label: 'В процессе', className: 'learning' },
  { value: 'mastered', label: 'Освоено', className: 'mastered' },
]

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
      setSaveError(error instanceof Error ? error.message : 'Не удалось обновить статус')
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
      setSaveError(error instanceof Error ? error.message : 'Не удалось сохранить заметку')
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
          {isSavingTitle ? <p className="status-text">Сохраняю название...</p> : null}
          {titleError ? <p className="error-text">{titleError}</p> : null}
        </div>
        <button className="secondary" onClick={() => void handleBack()}>
          Панель управления
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
                Статус изучения
                <div className="status-switcher" role="group" aria-label="Статус изучения навыка">
                  {STATUS_OPTIONS.map((option) => {
                    const currentStatus = plan.skill_statuses[selectedSkill.id] ?? 'unknown'
                    const isActive = currentStatus === option.value
                    return (
                      <button
                        key={option.value}
                        type="button"
                        className={`status-switcher-btn ${option.className} ${isActive ? 'active' : ''}`}
                        onClick={() => void handleStatusChange(option.value)}
                      >
                        {option.label}
                      </button>
                    )
                  })}
                </div>
              </label>
              <label>
                Заметки
                <textarea
                  rows={9}
                  value={noteDraft}
                  onChange={(event) => setNoteDraft(event.target.value)}
                  placeholder="Личные заметки по навыку..."
                />
              </label>
              {isSavingNote ? <p className="status-text">Сохраняю заметку...</p> : null}
              {saveError ? <p className="error-text">{saveError}</p> : null}
            </section>
          </aside>
        ) : null}
      </div>
    </main>
  )
}
