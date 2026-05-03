import heapq

from backend.domain.learning_goal import LearningGoal
from backend.domain.learning_plan import LearningPlan
from backend.domain.learning_step import LearningStep
from backend.domain.skill_graph import SkillGraph
from backend.domain.user_knowledge import UserKnowledge


class PlanService:
    def build_plan(
        self,
        graph: SkillGraph,
        goal: LearningGoal,
        knowledge: UserKnowledge,
    ) -> LearningPlan:
        """
        Build a learning plan for target goals.

        Priority for skills that are available at the same time:
            1) depth (asc)
            2) difficulty (asc)
            3) skill_id (asc, deterministic tie-breaker)
        """
        subgraph = graph.get_subgraph(goal.target_skill_ids, goal.mode)
        required = set(subgraph.skills.keys())
        mastered = knowledge.mastered_ids()
        required -= mastered

        if not required:
            return LearningPlan(
                id=None,
                user_id=knowledge.user_id,
                goal=goal,
                ordered_skill_ids=[],
                steps=[],
            )

        ordered = self._topological_sort_by_priority(graph=subgraph, subset=required)
        steps = self._build_steps_for_skills(ordered)
        return LearningPlan(
            id=None,
            user_id=knowledge.user_id,
            goal=goal,
            ordered_skill_ids=ordered,
            steps=steps,
        )

    def _build_steps_for_skills(self, ordered_skill_ids: list[str]) -> list[LearningStep]:
        steps: list[LearningStep] = []
        for skill_id in ordered_skill_ids:
            steps.append(
                LearningStep(
                    id=f"{skill_id}:theory",
                    skill_id=skill_id,
                    title=f"Изучи теорию: {skill_id}",
                    type="theory",
                    estimate_min=30,
                    acceptance_criteria="Кратко объясняет ключевые понятия своими словами.",
                )
            )
            steps.append(
                LearningStep(
                    id=f"{skill_id}:practice",
                    skill_id=skill_id,
                    title=f"Практика: {skill_id}",
                    type="practice",
                    estimate_min=45,
                    acceptance_criteria="Выполнено практическое задание по теме без критических ошибок.",
                )
            )
            steps.append(
                LearningStep(
                    id=f"{skill_id}:checkpoint",
                    skill_id=skill_id,
                    title=f"Проверка: {skill_id}",
                    type="checkpoint",
                    estimate_min=20,
                    acceptance_criteria="Результат проверен и подтвержден критериями готовности.",
                )
            )
        return steps

    def _topological_sort_by_priority(self, graph: SkillGraph, subset: set[str]) -> list[str]:
        in_degree = {skill_id: 0 for skill_id in subset}
        for skill_id in subset:
            in_degree[skill_id] = len(
                [prereq for prereq in graph.prerequisites_map[skill_id] if prereq in subset]
            )

        heap = []
        for skill_id, degree in in_degree.items():
            if degree == 0:
                skill = graph.skills[skill_id]
                heapq.heappush(heap, (graph.get_depth(skill_id), skill.difficulty, skill_id))

        ordered = []

        while heap:
            _, _, current = heapq.heappop(heap)
            ordered.append(current)

            for dependent in graph.dependents_map[current]:
                if dependent not in subset:
                    continue

                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    skill = graph.skills[dependent]
                    heapq.heappush(
                        heap,
                        (graph.get_depth(dependent), skill.difficulty, dependent),
                    )

        if len(ordered) != len(subset):
            raise ValueError("Graph contains a cycle!")

        return ordered
