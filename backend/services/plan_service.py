import heapq

from backend.domain.learning_goal import LearningGoal
from backend.domain.learning_plan import LearningPlan
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
        required = self._collect_required_skills(graph=graph, goal=goal)
        mastered = knowledge.mastered_ids()
        required -= mastered

        if not required:
            return LearningPlan(
                user_id=knowledge.user_id,
                goal=goal,
                ordered_skill_ids=[],
            )

        ordered = self._topological_sort_by_priority(graph=graph, subset=required)
        return LearningPlan(
            user_id=knowledge.user_id,
            goal=goal,
            ordered_skill_ids=ordered,
        )

    def _collect_required_skills(self, graph: SkillGraph, goal: LearningGoal) -> set[str]:
        required = set()

        # Modes can be expanded later; for now every mode uses full transitive closure.
        for goal_id in goal.target_skill_ids:
            if goal_id not in graph.skills:
                raise ValueError(f"No such skill: {goal_id}")

            required.update(graph.get_transitive_deps(goal_id))
            required.add(goal_id)

        return required

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
