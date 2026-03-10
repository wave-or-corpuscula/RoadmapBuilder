from uuid import uuid4

from backend.domain.learning_plan import LearningPlan


class InMemoryPlanRepository:
    def __init__(self):
        self._plans: dict[str, LearningPlan] = {}

    def save(self, plan: LearningPlan) -> LearningPlan:
        if plan.id is None:
            plan = plan.with_id(str(uuid4()))

        self._plans[plan.id] = plan
        return plan

    def get(self, plan_id: str) -> LearningPlan | None:
        return self._plans.get(plan_id)
