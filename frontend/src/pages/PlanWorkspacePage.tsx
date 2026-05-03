import { useEffect, useMemo, useRef, useState } from 'react'

import PlanGraphView from '../components/PlanGraphView'
import type { KnowledgeStatus, Plan, PlanGraph } from '../shared/types/api'

type Props = {
  plan: Plan
  graph: PlanGraph
  nextStepSkillId: string | null
  plans: Plan[]
  onBack: () => void
  onOpenPlan: (planId: string) => Promise<void>
  onDeletePlan: (planId: string, fallbackPlanId: string | null) => Promise<void>
  onCreateDerivedPlan: (planId: string, skillId: string) => Promise<Plan>
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
  nextStepSkillId,
  plans,
  onBack,
  onOpenPlan,
  onDeletePlan,
  onCreateDerivedPlan,
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
  const [isPlansMenuOpen, setIsPlansMenuOpen] = useState(false)
  const [expandedPlanIds, setExpandedPlanIds] = useState<Set<string>>(new Set())
  const [isCreatingDerived, setIsCreatingDerived] = useState(false)
  const [deriveError, setDeriveError] = useState<string | null>(null)
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

  useEffect(() => {
    setIsPlansMenuOpen(false)
    setDeriveError(null)
  }, [plan.id])

  const planById = useMemo<Map<string, Plan>>(
    () => new Map<string, Plan>(plans.map((item) => [item.id, item])),
    [plans],
  )

  const rootPlan = useMemo(() => {
    let current: Plan | null = plan
    const visited = new Set<string>()
    while (current?.parent_plan_id) {
      if (visited.has(current.id)) {
        break
      }
      visited.add(current.id)
      const parent: Plan | null = planById.get(current.parent_plan_id) ?? null
      if (!parent) {
        break
      }
      current = parent
    }
    return current
  }, [plan, planById])

  const childrenByParent = useMemo(() => {
    const map = new Map<string, Plan[]>()
    for (const item of plans) {
      const parentId = item.parent_plan_id
      if (!parentId) {
        continue
      }
      const bucket = map.get(parentId) ?? []
      bucket.push(item)
      map.set(parentId, bucket)
    }
    for (const bucket of map.values()) {
      bucket.sort((left, right) => left.title.localeCompare(right.title))
    }
    return map
  }, [plans])

  useEffect(() => {
    const start = rootPlan ?? plan
    const expanded = new Set<string>([start.id])
    let current: Plan | null = plan
    const visited = new Set<string>()
    while (current?.parent_plan_id) {
      if (visited.has(current.id)) {
        break
      }
      visited.add(current.id)
      expanded.add(current.parent_plan_id)
      const parent: Plan | null = planById.get(current.parent_plan_id) ?? null
      if (!parent) {
        break
      }
      current = parent
    }
    setExpandedPlanIds(expanded)
  }, [plan, planById, rootPlan])

  const selectedSkill = useMemo(
    () => graph.skills.find((item) => item.id === selectedSkillId) ?? null,
    [graph.skills, selectedSkillId],
  )
  const nextStepSkill = useMemo(
    () => graph.skills.find((item) => item.id === nextStepSkillId) ?? null,
    [graph.skills, nextStepSkillId],
  )
  const isSelectedSkillRoot = selectedSkill ? selectedSkill.prerequisites.length === 0 : false

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
      setIsPlansMenuOpen(false)
      setSaveError(null)
      setDeriveError(null)
    })()
  }

  function toggleExpand(planId: string) {
    setExpandedPlanIds((prev) => {
      const next = new Set(prev)
      if (next.has(planId)) {
        next.delete(planId)
      } else {
        next.add(planId)
      }
      return next
    })
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

  async function handleOpenPlan(planId: string) {
    await flushCurrentNote()
    setIsPlansMenuOpen(false)
    await onOpenPlan(planId)
  }

  async function handleCreateDerivedFromSelectedSkill() {
    if (!selectedSkillId) {
      return
    }
    if (isSelectedSkillRoot) {
      setDeriveError('Корневой навык нельзя сделать целью подплана')
      return
    }
    try {
      setIsCreatingDerived(true)
      setDeriveError(null)
      await flushCurrentNote()
      await onCreateDerivedPlan(plan.id, selectedSkillId)
    } catch (error) {
      setDeriveError(error instanceof Error ? error.message : 'Не удалось создать подплан')
    } finally {
      setIsCreatingDerived(false)
    }
  }

  async function handleDeletePlan(target: Plan) {
    const childrenCount = (childrenByParent.get(target.id) ?? []).length
    const hasChildren = childrenCount > 0
    const message = hasChildren
      ? `Удалить подплан "${target.title}" и все его дочерние планы?`
      : `Удалить подплан "${target.title}"?`
    if (!window.confirm(message)) {
      return
    }
    await flushCurrentNote()
    await onDeletePlan(target.id, target.parent_plan_id ?? null)
    setIsPlansMenuOpen(false)
  }

  return (
    <main className="plan-workspace">
      <header className="workspace-topbar">
        <div className="workspace-plan-nav">
          <button
            type="button"
            className="plans-toggle-text"
            onClick={() => setIsPlansMenuOpen((prev) => !prev)}
            aria-expanded={isPlansMenuOpen}
          >
            <span className="plans-toggle-caret">{isPlansMenuOpen ? '▾' : '▸'}</span>
            <span className="plans-toggle-label">Планы</span>
          </button>
          {isPlansMenuOpen ? (
            <section className="plans-menu card">
              <h3>Иерархия планов</h3>
              <div className="plans-menu-section">
                <ul className="plans-tree-list">
                  {(function renderTree(node: Plan, depth: number) {
                    const children = childrenByParent.get(node.id) ?? []
                    const hasChildren = children.length > 0
                    const isExpanded = expandedPlanIds.has(node.id)
                    return (
                      <li key={node.id}>
                        <div className="plans-tree-row" style={{ paddingLeft: `${depth * 14}px` }}>
                          <button
                            type="button"
                            className={`plans-disclosure ${hasChildren ? 'visible' : ''}`}
                            onClick={() => toggleExpand(node.id)}
                            aria-label={isExpanded ? 'Свернуть ветку' : 'Развернуть ветку'}
                            disabled={!hasChildren}
                          >
                            {hasChildren ? (isExpanded ? '▾' : '▸') : ''}
                          </button>
                          <button
                            className={`plans-tree-item ${node.id === plan.id ? 'active' : ''}`}
                            onClick={() => void handleOpenPlan(node.id)}
                          >
                            <span>{node.title}</span>
                            {node.id === plan.id ? <small>текущий</small> : null}
                            {depth === 0 ? <small>корень</small> : null}
                            {depth > 0 && node.id !== plan.id ? <small>подплан</small> : null}
                          </button>
                          {depth > 0 ? (
                            <button
                              type="button"
                              className="plans-delete-action"
                              onClick={(event) => {
                                event.stopPropagation()
                                void handleDeletePlan(node)
                              }}
                            >
                              Удалить
                            </button>
                          ) : null}
                        </div>
                        {hasChildren && isExpanded ? (
                          <ul className="plans-tree-list">
                            {children.map((child) => renderTree(child, depth + 1))}
                          </ul>
                        ) : null}
                      </li>
                    )
                  })(rootPlan ?? plan, 0)}
                </ul>
              </div>
            </section>
          ) : null}
        </div>
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
          {nextStepSkill ? (
            <button
              type="button"
              className="next-step-cta"
              onClick={() => handleSelectSkill(nextStepSkill.id)}
            >
              Продолжить: {nextStepSkill.title}
            </button>
          ) : (
            <p className="status-text">Все шаги в этом плане уже отмечены</p>
          )}
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
              {deriveError ? <p className="error-text">{deriveError}</p> : null}
              <button
                className="compact derive-goal-btn"
                type="button"
                onClick={() => void handleCreateDerivedFromSelectedSkill()}
                disabled={isCreatingDerived || isSelectedSkillRoot}
              >
                {isCreatingDerived
                  ? 'Создаю подплан...'
                  : isSelectedSkillRoot
                    ? 'Корневой навык'
                    : 'Сделать целью'}
              </button>
            </section>
          </aside>
        ) : null}
      </div>
    </main>
  )
}
