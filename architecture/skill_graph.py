from collections import defaultdict, deque
from uuid import UUID

from app.domain.enums import LearningMode
from app.domain.skill import Skill


class CycleDetectedError(Exception):
    """Граф содержит цикл — недопустимо для DAG."""


class SkillNotFoundError(Exception):
    """Навык не найден в графе."""


class SkillGraph:
    """
    Направленный ациклический граф (DAG) навыков.
    Ребро A → B означает: A является prerequisites для B.

    Это центральная доменная сущность системы.
    Содержит все алгоритмы работы с графом.
    """

    def __init__(self, skills: list[Skill]) -> None:
        self._skills: dict[UUID, Skill] = {s.id: s for s in skills}
        self._validate_no_cycles()
        self._depth_cache: dict[UUID, int] = {}

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def get_skill(self, skill_id: UUID) -> Skill:
        if skill_id not in self._skills:
            raise SkillNotFoundError(f"Skill {skill_id} not found in graph")
        return self._skills[skill_id]

    def all_skills(self) -> list[Skill]:
        return list(self._skills.values())

    def get_transitive_deps(self, skill_id: UUID, mode: LearningMode) -> set[UUID]:
        """
        Возвращает все зависимости навыка с учётом режима обучения.

        SURFACE  — только прямые prerequisites (глубина 1)
        BALANCED — транзитивные зависимости (полный BFS)
        DEEP     — то же, что BALANCED (расширяется при добавлении optional links)
        """
        self._ensure_exists(skill_id)

        if mode == LearningMode.SURFACE:
            return set(self._skills[skill_id].prerequisites)

        # BALANCED / DEEP — полный BFS
        visited: set[UUID] = set()
        queue: deque[UUID] = deque(self._skills[skill_id].prerequisites)

        while queue:
            dep_id = queue.popleft()
            if dep_id in visited:
                continue
            visited.add(dep_id)
            if dep_id in self._skills:
                queue.extend(self._skills[dep_id].prerequisites)

        return visited

    def get_subgraph(self, target_ids: list[UUID], mode: LearningMode) -> "SkillGraph":
        """
        Извлекает подграф, необходимый для достижения указанных целей.
        Объединяет транзитивные зависимости всех целей (без дубликатов).
        """
        all_nodes: set[UUID] = set()

        for target_id in target_ids:
            self._ensure_exists(target_id)
            deps = self.get_transitive_deps(target_id, mode)
            all_nodes.update(deps)
            all_nodes.add(target_id)

        included_skills = [
            Skill(
                id=s.id,
                title=s.title,
                description=s.description,
                difficulty=s.difficulty,
                # Исключаем зависимости, которые не входят в подграф
                prerequisites=frozenset(p for p in s.prerequisites if p in all_nodes),
            )
            for node_id in all_nodes
            if (s := self._skills.get(node_id)) is not None
        ]

        return SkillGraph(included_skills)

    def topological_sort(self) -> list[list[Skill]]:
        """
        Топологическая сортировка методом Кана (BFS).
        Возвращает список уровней: каждый уровень — навыки, доступные одновременно.
        Внутри уровня навыки отсортированы по depth ASC, difficulty ASC.
        """
        in_degree: dict[UUID, int] = defaultdict(int)

        for skill in self._skills.values():
            if skill.id not in in_degree:
                in_degree[skill.id] = 0
            for prereq_id in skill.prerequisites:
                in_degree[skill.id] += 1

        levels: list[list[Skill]] = []
        queue: deque[UUID] = deque(
            skill_id for skill_id, degree in in_degree.items() if degree == 0
        )

        while queue:
            level_size = len(queue)
            level_skills: list[Skill] = []

            for _ in range(level_size):
                skill_id = queue.popleft()
                level_skills.append(self._skills[skill_id])

                # Уменьшить in_degree у "зависимых" навыков
                for skill in self._skills.values():
                    if skill_id in skill.prerequisites:
                        in_degree[skill.id] -= 1
                        if in_degree[skill.id] == 0:
                            queue.append(skill.id)

            # Сортировка внутри уровня: глубина ↑, сложность ↑
            level_skills.sort(key=lambda s: (self.get_depth(s.id), s.difficulty))
            levels.append(level_skills)

        return levels

    def topological_sort_flat(self) -> list[Skill]:
        """Плоский список навыков в топологическом порядке."""
        return [skill for level in self.topological_sort() for skill in level]

    def get_depth(self, skill_id: UUID) -> int:
        """
        Глубина узла = длина самого длинного пути от корня до узла.
        Кэшируется после первого вычисления.
        """
        if skill_id in self._depth_cache:
            return self._depth_cache[skill_id]

        skill = self._skills.get(skill_id)
        if skill is None:
            return 0

        if not skill.prerequisites:
            depth = 0
        else:
            depth = 1 + max(self.get_depth(prereq_id) for prereq_id in skill.prerequisites)

        self._depth_cache[skill_id] = depth
        return depth

    def size(self) -> int:
        return len(self._skills)

    # ------------------------------------------------------------------ #
    # Validation                                                           #
    # ------------------------------------------------------------------ #

    def _validate_no_cycles(self) -> None:
        """DFS-проверка на отсутствие циклов в DAG."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[UUID, int] = {sid: WHITE for sid in self._skills}

        def dfs(node_id: UUID) -> None:
            color[node_id] = GRAY
            for prereq_id in self._skills[node_id].prerequisites:
                if prereq_id not in color:
                    continue  # Зависимость вне графа — игнорируем
                if color[prereq_id] == GRAY:
                    raise CycleDetectedError(
                        f"Cycle detected involving skill {node_id} → {prereq_id}"
                    )
                if color[prereq_id] == WHITE:
                    dfs(prereq_id)
            color[node_id] = BLACK

        for skill_id in self._skills:
            if color[skill_id] == WHITE:
                dfs(skill_id)

    def _ensure_exists(self, skill_id: UUID) -> None:
        if skill_id not in self._skills:
            raise SkillNotFoundError(f"Skill {skill_id} not found")
