import type { KnowledgeStatus, Plan, PlanGraph } from '../shared/types/api'

type Props = {
  graph: PlanGraph
  plan: Plan
  selectedSkillId: string | null
  onSelectSkill: (skillId: string) => void
  onStatusChange: (skillId: string, status: KnowledgeStatus) => void
}

type NodePosition = {
  x: number
  y: number
}

const NODE_WIDTH = 220
const NODE_HEIGHT = 108
const H_GAP = 140
const V_GAP = 40
const PADDING_X = 30
const PADDING_Y = 30

function computeDepths(graph: PlanGraph): Record<string, number> {
  const byId = new Map(graph.skills.map((skill) => [skill.id, skill]))
  const memo = new Map<string, number>()

  function depth(skillId: string): number {
    if (memo.has(skillId)) {
      return memo.get(skillId) as number
    }
    const skill = byId.get(skillId)
    if (!skill || skill.prerequisites.length === 0) {
      memo.set(skillId, 0)
      return 0
    }
    const value = 1 + Math.max(...skill.prerequisites.map((prerequisite) => depth(prerequisite)))
    memo.set(skillId, value)
    return value
  }

  const result: Record<string, number> = {}
  for (const skill of graph.skills) {
    result[skill.id] = depth(skill.id)
  }
  return result
}

function computePositions(graph: PlanGraph): Record<string, NodePosition> {
  const depths = computeDepths(graph)
  const columns: Record<number, string[]> = {}

  for (const skill of graph.skills) {
    const depth = depths[skill.id]
    if (!columns[depth]) {
      columns[depth] = []
    }
    columns[depth].push(skill.id)
  }

  const positions: Record<string, NodePosition> = {}
  for (const [depthRaw, skillIds] of Object.entries(columns)) {
    const depth = Number(depthRaw)
    skillIds.sort()

    skillIds.forEach((skillId, index) => {
      positions[skillId] = {
        x: PADDING_X + depth * (NODE_WIDTH + H_GAP),
        y: PADDING_Y + index * (NODE_HEIGHT + V_GAP),
      }
    })
  }
  return positions
}

function statusClass(status: KnowledgeStatus, selected: boolean): string {
  const selectedClass = selected ? ' selected' : ''
  if (status === 'mastered') {
    return `graph-node mastered${selectedClass}`
  }
  if (status === 'learning') {
    return `graph-node learning${selectedClass}`
  }
  return `graph-node unknown${selectedClass}`
}

export default function PlanGraphView({ graph, plan, selectedSkillId, onSelectSkill, onStatusChange }: Props) {
  const positions = computePositions(graph)
  const maxX = Math.max(...Object.values(positions).map((value) => value.x), 0) + NODE_WIDTH + PADDING_X
  const maxY = Math.max(...Object.values(positions).map((value) => value.y), 0) + NODE_HEIGHT + PADDING_Y

  return (
    <div className="graph-scroll">
      <div className="graph-stage" style={{ width: `${maxX}px`, height: `${maxY}px` }}>
        <svg className="graph-edges" width={maxX} height={maxY}>
          {graph.skills.flatMap((skill) =>
            skill.prerequisites.map((prerequisite) => {
              const from = positions[prerequisite]
              const to = positions[skill.id]
              if (!from || !to) {
                return null
              }
              const x1 = from.x + NODE_WIDTH
              const y1 = from.y + NODE_HEIGHT / 2
              const x2 = to.x
              const y2 = to.y + NODE_HEIGHT / 2
              return (
                <path
                  key={`${prerequisite}->${skill.id}`}
                  d={`M${x1},${y1} C ${x1 + 42},${y1} ${x2 - 42},${y2} ${x2},${y2}`}
                  fill="none"
                  stroke="#95a3bf"
                  strokeWidth={2}
                />
              )
            }),
          )}
        </svg>

        {graph.skills.map((skill) => {
          const position = positions[skill.id]
          if (!position) {
            return null
          }
          const status = plan.skill_statuses[skill.id] ?? 'unknown'
          const isSelected = skill.id == selectedSkillId
          return (
            <article
              key={skill.id}
              className={statusClass(status, isSelected)}
              onClick={() => onSelectSkill(skill.id)}
              style={{
                left: `${position.x}px`,
                top: `${position.y}px`,
                width: `${NODE_WIDTH}px`,
                minHeight: `${NODE_HEIGHT}px`,
              }}
            >
              <header>
                <h3>{skill.title}</h3>
              </header>
              <p>{skill.description}</p>
              <select value={status} onChange={(event) => onStatusChange(skill.id, event.target.value as KnowledgeStatus)}>
                <option value="unknown">unknown</option>
                <option value="learning">learning</option>
                <option value="mastered">mastered</option>
              </select>
            </article>
          )
        })}
      </div>
    </div>
  )
}
