import { useEffect, useMemo, useState } from 'react'

import PlanGraphView from '../components/PlanGraphView'
import type { KnowledgeStatus, Plan, PlanGraph } from '../shared/types/api'

type Props = {
  plan: Plan
  graph: PlanGraph
  onBack: () => void
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
  onUpdatePlanSkillStatus,
  onUpdatePlanSkillNote,
}: Props) {
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null)
  const [noteDraft, setNoteDraft] = useState('')
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    if (!selectedSkillId || !graph.skills.find((item) => item.id === selectedSkillId)) {
      const first = graph.skills[0]
      setSelectedSkillId(first ? first.id : null)
    }
  }, [graph, selectedSkillId])

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

  async function handleStatusChange(skillId: string, status: KnowledgeStatus) {
    try {
      await onUpdatePlanSkillStatus(plan.id, skillId, status)
      setSaveError(null)
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to update status')
    }
  }

  async function handleSaveNote() {
    if (!selectedSkillId) {
      return
    }
    try {
      await onUpdatePlanSkillNote(plan.id, selectedSkillId, noteDraft)
      setSaveError(null)
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save note')
    }
  }

  return (
    <main className="plan-workspace">
      <header className="workspace-topbar">
        <div>
          <h1>{plan.title}</h1>
          <p>Основной режим работы с планом.</p>
        </div>
        <button className="secondary" onClick={onBack}>
          Back to dashboard
        </button>
      </header>
      <div className="workspace-body">
        <aside className="workspace-sidebar">
          <section className="card">
            <h2>Node Notes</h2>
            {selectedSkill ? (
              <>
                <p>
                  <strong>{selectedSkill.title}</strong>
                </p>
                <textarea
                  rows={10}
                  value={noteDraft}
                  onChange={(event) => setNoteDraft(event.target.value)}
                  placeholder="Markdown notes..."
                />
                <div className="actions">
                  <button type="button" onClick={() => void handleSaveNote()}>
                    Save note
                  </button>
                </div>
                <div className="markdown-preview" dangerouslySetInnerHTML={{ __html: renderMarkdownPreview(noteDraft) }} />
              </>
            ) : (
              <p>Select a node.</p>
            )}
            {saveError ? <p className="error-text">{saveError}</p> : null}
          </section>
        </aside>
        <section className="workspace-main">
          <PlanGraphView
            graph={graph}
            plan={plan}
            selectedSkillId={selectedSkillId}
            onSelectSkill={setSelectedSkillId}
            onStatusChange={handleStatusChange}
          />
        </section>
      </div>
    </main>
  )
}
