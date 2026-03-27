export type LearningMode = 'surface' | 'balanced' | 'deep'

export type KnowledgeStatus = 'unknown' | 'learning' | 'mastered'

export type AuthTokens = {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export type User = {
  id: string
  email: string
  display_name: string
}

export type Plan = {
  id: string
  user_id: string
  title: string
  goal: {
    target_skill_ids: string[]
    mode: LearningMode
  }
  ordered_skill_ids: string[]
  skill_statuses: Record<string, KnowledgeStatus>
  skill_notes: Record<string, string>
  created_at: string
  is_active: boolean
}

export type PlanGraphSkill = {
  id: string
  title: string
  description: string
  difficulty: number
  prerequisites: string[]
}

export type PlanGraph = {
  skills: PlanGraphSkill[]
}

export type Progress = {
  user_id: string
  statuses: Record<string, KnowledgeStatus>
}

export type ImportPlanPayload = {
  schema_version?: string
  title?: string
  skills: PlanGraphSkill[]
  target_skill_ids: string[]
  mode: LearningMode
  mastered_skill_ids?: string[]
}

export type ImportTemplate = {
  schema_version: string
  title: string
  skills: PlanGraphSkill[]
  target_skill_ids: string[]
  mode: LearningMode
  mastered_skill_ids: string[]
}

export type ImportPrompt = {
  schema_version: string
  topic: string
  prompt: string
}
