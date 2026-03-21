import { apiRequest } from './client'
import type { KnowledgeStatus, LearningMode, Plan, Progress } from '../types/api'

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
