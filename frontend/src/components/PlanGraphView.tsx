import { useMemo } from 'react'

import ReactFlow, {
  Background,
  Controls,
  Handle,
  Position,
  type Edge,
  type Node,
  type NodeMouseHandler,
  type NodeProps,
} from 'reactflow'
import 'reactflow/dist/style.css'

import type { Plan, PlanGraph } from '../shared/types/api'

type Props = {
  graph: PlanGraph
  plan: Plan
  selectedSkillId: string | null
  onSelectSkill: (skillId: string | null) => void
}

type NodePosition = {
  x: number
  y: number
}

type PlanNodeData = {
  title: string
  description: string
}

const NODE_WIDTH = 220
const NODE_HEIGHT = 132
const H_GAP = 140
const V_GAP = 74
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

function statusClass(status: Plan['skill_statuses'][string], selected: boolean): string {
  const selectedClass = selected ? ' selected' : ''
  if (status === 'mastered') {
    return `plan-node mastered${selectedClass}`
  }
  if (status === 'learning') {
    return `plan-node learning${selectedClass}`
  }
  return `plan-node unknown${selectedClass}`
}

function statusEdgeColor(status: Plan['skill_statuses'][string]): string {
  if (status === 'mastered') {
    return '#2c8f4a'
  }
  if (status === 'learning') {
    return '#d49a29'
  }
  return '#2f6fda'
}

function PlanNode({ data }: NodeProps<PlanNodeData>) {
  return (
    <div className="plan-node-content">
      <Handle id="target-left" type="target" position={Position.Left} className="plan-side-handle" />
      <h3>{data.title}</h3>
      <p>{data.description}</p>
      <Handle id="source-right" type="source" position={Position.Right} className="plan-side-handle" />
    </div>
  )
}

export default function PlanGraphView({ graph, plan, selectedSkillId, onSelectSkill }: Props) {
  const positions = useMemo(() => computePositions(graph), [graph])
  const nodeTypes = useMemo(() => ({ planNode: PlanNode }), [])

  const nodes = useMemo<Node<PlanNodeData>[]>(
    () =>
      graph.skills.map((skill) => {
        const position = positions[skill.id] ?? { x: 0, y: 0 }
        const status = plan.skill_statuses[skill.id] ?? 'unknown'
        const isSelected = skill.id === selectedSkillId
        return {
          id: skill.id,
          position,
          type: 'planNode',
          className: statusClass(status, isSelected),
          style: { width: NODE_WIDTH, height: NODE_HEIGHT },
          data: {
            title: skill.title,
            description: skill.description,
          },
          draggable: false,
          selectable: false,
        }
      }),
    [graph.skills, plan.skill_statuses, positions, selectedSkillId],
  )

  const edges = useMemo<Edge[]>(
    () =>
      graph.skills.flatMap((skill) =>
        skill.prerequisites.map((prerequisite) => {
          const isHighlighted =
            selectedSkillId !== null &&
            (prerequisite === selectedSkillId || skill.id === selectedSkillId)
          const targetStatus = plan.skill_statuses[skill.id] ?? 'unknown'
          const edgeColor = statusEdgeColor(targetStatus)

          return {
            id: `${prerequisite}->${skill.id}`,
            source: prerequisite,
            target: skill.id,
            sourceHandle: 'source-right',
            targetHandle: 'target-left',
            animated: false,
            style: {
              stroke: edgeColor,
              strokeWidth: isHighlighted ? 3 : 2,
              opacity: selectedSkillId !== null && !isHighlighted ? 0.35 : 1,
            },
            type: 'default',
          }
        }),
      ),
    [graph.skills, selectedSkillId],
  )

  const handleNodeClick: NodeMouseHandler = (_event, node) => {
    if (node.id === selectedSkillId) {
      onSelectSkill(null)
      return
    }
    onSelectSkill(node.id)
  }

  return (
    <div className="graph-flow-shell">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.25, minZoom: 0.35 }}
        minZoom={0.2}
        maxZoom={1.8}
        panOnDrag
        panOnScroll={false}
        zoomOnScroll
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        onPaneClick={() => onSelectSkill(null)}
        onNodeClick={handleNodeClick}
      >
        <Background color="#e4ebf8" gap={24} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}
