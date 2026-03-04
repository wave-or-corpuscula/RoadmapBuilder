import uuid
from datetime import datetime

from app.domain.enums import KnowledgeStatus, LearningMode, PlanStatus
from app.domain.learning_plan import LearningPlan, PlanSkill
from app.domain.skill import Skill
from app.domain.skill_graph import SkillGraph
from app.repositories.skill_repository import SkillRepository
from app.repositories.plan_repository import PlanRepository


class PlanService:
    """
    Оркестрирует построение и управление планами обучения.
    Центральный сервис системы.
    """

    def __init__(
        self,
        skill_repo: SkillRepository,
        plan_repo: PlanRepository,
    ) -> None:
        self._skill_repo = skill_repo
        self._plan_repo = plan_repo

    async def build_plan(
        self,
        user_id: uuid.UUID,
        goal_skill_ids: list[uuid.UUID],
        mode: LearningMode,
        exclude_mastered: bool = True,
    ) -> LearningPlan:
        """
        Строит новый план обучения:
        1. Загружает полный граф навыков
        2. Извлекает подграф для целей
        3. Топологически сортирует
        4. Фиксирует план
        """
        # Загрузить все навыки и построить доменный граф
        all_skills = await self._skill_repo.get_all_with_prerequisites()
        graph = SkillGraph(all_skills)

        # Извлечь подграф для целей с учётом режима
        subgraph = graph.get_subgraph(goal_skill_ids, mode)

        # Получить плоский упорядоченный список навыков
        sorted_skills: list[Skill] = subgraph.topological_sort_flat()

        # Опционально исключить уже освоенные навыки
        if exclude_mastered:
            mastered_ids = await self._plan_repo.get_mastered_skill_ids(user_id)
            sorted_skills = [s for s in sorted_skills if s.id not in mastered_ids]

        # Построить план
        plan_skills = [
            PlanSkill(skill_id=skill.id, order_index=idx)
            for idx, skill in enumerate(sorted_skills)
        ]

        plan = LearningPlan(
            id=uuid.uuid4(),
            user_id=user_id,
            goal_skill_ids=goal_skill_ids,
            mode=mode,
            plan_skills=plan_skills,
            status=PlanStatus.ACTIVE,
            created_at=datetime.utcnow(),
            graph_version=await self._skill_repo.get_graph_version(),
        )

        # Деактивировать предыдущие активные планы
        await self._plan_repo.deactivate_user_plans(user_id)

        # Сохранить новый план
        return await self._plan_repo.save(plan)

    async def get_next_step(self, plan_id: uuid.UUID, user_id: uuid.UUID) -> uuid.UUID | None:
        plan = await self._plan_repo.get_by_id(plan_id, user_id)
        if plan is None:
            return None
        return plan.get_next_skill()

    async def update_skill_status(
        self,
        plan_id: uuid.UUID,
        skill_id: uuid.UUID,
        user_id: uuid.UUID,
        status: KnowledgeStatus,
    ) -> LearningPlan:
        plan = await self._plan_repo.get_by_id(plan_id, user_id)
        if plan is None:
            raise ValueError(f"Plan {plan_id} not found")

        plan.update_skill_status(skill_id, status)

        if plan.is_completed():
            plan.status = PlanStatus.COMPLETED

        return await self._plan_repo.save(plan)
