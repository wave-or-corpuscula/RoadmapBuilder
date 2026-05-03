import heapq
import re

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
        steps = self._build_steps_for_skills(subgraph, ordered)
        return LearningPlan(
            id=None,
            user_id=knowledge.user_id,
            goal=goal,
            ordered_skill_ids=ordered,
            steps=steps,
        )

    def _extract_actions_from_description(self, title: str, description: str) -> list[str]:
        source = (description or "").strip()
        if not source:
            return [f"Освоить тему: {title}"]

        lines = [line.strip(" -*\t") for line in source.splitlines() if line.strip()]
        chunks: list[str] = []
        for line in lines:
            parts = [part.strip() for part in re.split(r"[.;]", line) if part.strip()]
            chunks.extend(parts)

        cleaned = []
        seen = set()
        for chunk in chunks:
            normalized = chunk[0].upper() + chunk[1:] if len(chunk) > 1 else chunk.upper()
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(normalized)
            if len(cleaned) == 3:
                break

        if cleaned:
            return cleaned
        return [f"Освоить тему: {title}"]

    def _build_steps_for_skills(self, graph: SkillGraph, ordered_skill_ids: list[str]) -> list[LearningStep]:
        steps: list[LearningStep] = []
        for skill_id in ordered_skill_ids:
            skill = graph.skills[skill_id]
            actions = self._extract_actions_from_description(skill.title, skill.description)
            theory_action = actions[0]
            practice_action = actions[1] if len(actions) > 1 else actions[0]
            checkpoint_action = actions[2] if len(actions) > 2 else actions[-1]

            steps.append(
                LearningStep(
                    id=f"{skill_id}:theory",
                    skill_id=skill_id,
                    title=f"Разобрать: {theory_action}",
                    type="theory",
                    estimate_min=30,
                    acceptance_criteria=f"Пользователь объясняет пункт: {theory_action}",
                )
            )
            steps.append(
                LearningStep(
                    id=f"{skill_id}:practice",
                    skill_id=skill_id,
                    title=f"Сделать: {practice_action}",
                    type="practice",
                    estimate_min=45,
                    acceptance_criteria=f"Практически выполнен пункт: {practice_action}",
                )
            )
            steps.append(
                LearningStep(
                    id=f"{skill_id}:checkpoint",
                    skill_id=skill_id,
                    title=f"Проверка: {checkpoint_action}",
                    type="checkpoint",
                    estimate_min=20,
                    acceptance_criteria=f"Подтвержден результат по пункту: {checkpoint_action}",
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
