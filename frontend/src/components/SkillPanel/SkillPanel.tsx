import React, { useEffect, useState, useCallback } from 'react'

import { getSkillSteps, splitStep } from '../../shared/api/planApi'
import type { KnowledgeStatus, LearningStep } from '../../shared/types/api'

type SkillPanelProps = {
  planId: string
  skillId: string
  skillTitle: string
  token: string
  selectedStepId?: string | null
  onStepSelect?: (stepId: string | null) => void
  onStepStatusChange?: (stepId: string, status: KnowledgeStatus) => void
  onStepsChange?: () => void
}

function StepStatusIndicator({ status }: { status: KnowledgeStatus }) {
  const colors: Record<KnowledgeStatus, string> = {
    unknown: '#8ea0bf',
    learning: '#d49a29',
    mastered: '#22c55e',
  }
  return (
    <span
      className="step-status-dot"
      style={{ backgroundColor: colors[status] }}
      title={status}
    />
  )
}

export default function SkillPanel({ planId, skillId, skillTitle, token, selectedStepId: externalSelectedStepId, onStepSelect, onStepsChange }: SkillPanelProps) {
  const [steps, setSteps] = useState<LearningStep[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [splittingStepId, setSplittingStepId] = useState<string | null>(null)

  const [internalSelectedStepId, setInternalSelectedStepId] = useState<string | null>(null)
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set())

  const selectedStepId = externalSelectedStepId ?? internalSelectedStepId

  const loadSteps = useCallback(async () => {
    try {
      setLoading(true)
      const skillSteps = await getSkillSteps(token, planId, skillId)
      setSteps(skillSteps)
      // Default: expand first level (steps directly under skill)
      const firstLevelIds = new Set(skillSteps.map(s => s.id))
      setExpandedSteps(firstLevelIds)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load steps')
    } finally {
      setLoading(false)
    }
  }, [token, planId, skillId])

  useEffect(() => {
    if (skillId) {
      void loadSteps()
    }
  }, [skillId, loadSteps])

  // Auto-select first step when steps load and no external selection
  useEffect(() => {
    if (steps.length > 0 && !selectedStepId && !onStepSelect) {
      setInternalSelectedStepId(steps[0].id)
    }
  }, [steps, selectedStepId, onStepSelect])

  function toggleExpand(stepId: string) {
    setExpandedSteps(prev => {
      const next = new Set(prev)
      if (next.has(stepId)) {
        next.delete(stepId)
      } else {
        next.add(stepId)
      }
      return next
    })
  }

  function selectStep(stepId: string) {
    if (onStepSelect) {
      onStepSelect(stepId)
    } else {
      setInternalSelectedStepId(stepId)
    }
  }

  async function handleSplitStep(stepId: string) {
    try {
      setSplittingStepId(stepId)
      await splitStep(token, planId, stepId, [])
      await loadSteps()
      onStepsChange?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to split step')
    } finally {
      setSplittingStepId(null)
    }
  }

  function renderStepTree(step: LearningStep, depth = 0): React.ReactElement {
    const hasChildren = step.substeps.length > 0
    const isExpanded = expandedSteps.has(step.id)
    const isSelected = selectedStepId === step.id

    return (
      <div key={step.id} className="step-tree-item">
        <div
          className={`step-tree-row ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {hasChildren ? (
            <button
              type="button"
              className="step-expand-btn"
              onClick={(e) => { e.stopPropagation(); toggleExpand(step.id) }}
            >
              {isExpanded ? '▾' : '▸'}
            </button>
          ) : (
            <span className="step-expand-placeholder" />
          )}
          <button
            type="button"
            className="step-title-btn"
            onClick={() => selectStep(step.id)}
          >
            <StepStatusIndicator status={step.status} />
            <span>{step.title}</span>
          </button>
          {step.is_split && !hasChildren && (
            <button
              type="button"
              className="step-split-btn"
              onClick={() => handleSplitStep(step.id)}
              disabled={splittingStepId === step.id}
            >
              {splittingStepId === step.id ? '...' : 'Разбить'}
            </button>
          )}
        </div>
        {hasChildren && isExpanded && (
          <div className="step-children">
            {step.substeps.map(substep => renderStepTree(substep, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return <div className="skill-panel-loading">Загрузка шагов...</div>
  }

  if (error) {
    return <div className="skill-panel-error">Ошибка: {error}</div>
  }

  return (
    <div className="skill-panel">
      <button
        type="button"
        className="back-to-skill-btn"
        onClick={() => {
          if (onStepSelect) {
            onStepSelect(null);
          } else {
            setInternalSelectedStepId(null);
          }
        }}
        style={{
          background: 'none',
          border: '1px solid #dce4f2',
          borderRadius: '8px',
          padding: '8px 12px',
          marginBottom: '12px',
          cursor: 'pointer',
          color: '#223a5e',
          fontWeight: '600',
          fontSize: '0.9rem'
        }}
      >
        {skillTitle}
      </button>
      <h3>Шаги</h3>
      {steps.length === 0 ? (
        <p className="no-steps">Шагов пока нет</p>
      ) : (
        <div className="step-tree">
          {steps.map(step => renderStepTree(step))}
        </div>
      )}
    </div>
  )
}