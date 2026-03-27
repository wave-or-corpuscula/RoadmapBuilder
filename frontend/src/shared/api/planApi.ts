import { apiRequest } from './client'
import type {
  ImportPlanPayload,
  ImportPrompt,
  ImportTemplate,
  KnowledgeStatus,
  LearningMode,
  Plan,
  PlanGraph,
  Progress,
} from '../types/api'

export function createPlan(
  token: string,
  targetSkillIds: string[],
  mode: LearningMode,
  masteredSkillIds?: string[],
): Promise<Plan> {
  return apiRequest<Plan>('/plans', {
    method: 'POST',
    token,
    body: {
      target_skill_ids: targetSkillIds,
      mode,
      mastered_skill_ids: masteredSkillIds,
    },
  })
}

export function importPlan(token: string, payload: ImportPlanPayload): Promise<Plan> {
  return apiRequest<Plan>('/plans/import', {
    method: 'POST',
    token,
    body: payload,
  })
}

export function getImportTemplate(): Promise<ImportTemplate> {
  return apiRequest<ImportTemplate>('/plans/import-template')
}

export function getImportPrompt(topic: string): Promise<ImportPrompt> {
  return apiRequest<ImportPrompt>('/plans/import-prompt', {
    method: 'POST',
    body: { topic },
  })
}

export function getPlanGraph(token: string, planId: string): Promise<PlanGraph> {
  return apiRequest<PlanGraph>(`/plans/${planId}/graph`, { token })
}

export function getPlan(token: string, planId: string): Promise<Plan> {
  return apiRequest<Plan>(`/plans/${planId}`, { token })
}

export function listPlans(token: string): Promise<Plan[]> {
  return apiRequest<Plan[]>('/plans', { token })
}

export function updatePlanSkillStatus(token: string, planId: string, skillId: string, status: KnowledgeStatus): Promise<Plan> {
  return apiRequest<Plan>(`/plans/${planId}/skills/${skillId}/status`, {
    method: 'PATCH',
    token,
    body: { status },
  })
}

export function updatePlanSkillNote(token: string, planId: string, skillId: string, note: string): Promise<Plan> {
  return apiRequest<Plan>(`/plans/${planId}/skills/${skillId}/note`, {
    method: 'PATCH',
    token,
    body: { note },
  })
}

export function getProgress(token: string): Promise<Progress> {
  return apiRequest<Progress>('/progress/me', { token })
}

export function updateProgressSkill(token: string, skillId: string, status: KnowledgeStatus): Promise<Progress> {
  return apiRequest<Progress>(`/progress/skills/${skillId}/status`, {
    method: 'PATCH',
    token,
    body: { status },
  })
}
