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

    def list_by_user(self, user_id: str) -> list[LearningPlan]:
        return [plan for plan in self._plans.values() if plan.user_id == user_id]

    def find_by_user_and_fingerprint(self, user_id: str, fingerprint: str) -> LearningPlan | None:
        for plan in self._plans.values():
            if plan.user_id == user_id and plan.fingerprint == fingerprint:
                return plan
        return None

    def delete(self, plan_id: str) -> None:
        if plan_id in self._plans:
            del self._plans[plan_id]
