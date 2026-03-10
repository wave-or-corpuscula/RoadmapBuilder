import json
from typing import Dict, Set
from collections import defaultdict
import heapq
from collections import deque

from .skill import Skill
from .enums import LearningMode


class SkillGraph:
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.dependents_map: Dict[str, Set[str]] = defaultdict(set)
        self.prerequisites_map: Dict[str, Set[str]] = defaultdict(set)
        self.depth_cache: Dict[str, int] = {}

    @classmethod
    def from_dict(cls, data: dict) -> "SkillGraph":
        """
        Create a SkillGraph instance from a dictionary.
        
        Args:
            data: Dictionary containing skill definitions with format:
                {
                    "skills": [
                        {
                            "id": str,
                            "title": str,
                            "description": str,
                            "difficulty": int,
                            "prerequisites": List[str]
                        },
                        ...
                    ]
                }
        
        Returns:
            SkillGraph: New graph instance with all skills and dependencies loaded
        
        Raises:
            ValueError: If duplicate skill IDs are found,
                    if prerequisite references non-existent skill,
                    or if graph contains cycles
        """
        graph = cls()

        for raw_skill in data["skills"]:
            skill_id = raw_skill["id"]

            if skill_id in graph.skills:
                raise ValueError(f"Duplicate skill with id: {skill_id}")

            skill = Skill(
                id=raw_skill["id"],
                title=raw_skill["title"],
                description=raw_skill["description"],
                difficulty=raw_skill["difficulty"],
            )

            graph.skills[skill_id] = skill

        for raw in data["skills"]:
            skill_id = raw["id"]
            for prereq in raw.get("prerequisites", []):
                if prereq not in graph.skills:
                    raise ValueError(f"Unknown prerequisite: {prereq} for {skill_id}")
                
                graph.prerequisites_map[skill_id].add(prereq)
                graph.dependents_map[prereq].add(skill_id)

        graph.validate_no_cycles()
        graph.recalculate_depth_cache()

        return graph

    @staticmethod
    def from_json(path: str) -> "SkillGraph":
        """
        Create a SkillGraph instance from a JSON file.
        
        Args:
            path: Path to JSON file containing skill definitions
                (format same as from_dict)
        
        Returns:
            SkillGraph: New graph instance with all skills and dependencies loaded
        
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
            ValueError: If duplicate skill IDs are found,
                    if prerequisite references non-existent skill,
                    or if graph contains cycles
        """
        with open(path) as file:
            data = json.load(file)

        return SkillGraph.from_dict(data)

    def add_skill(self, skill: Skill, prerequisites: list[str] | None = None):
        """
        Add a new skill with optional prerequisites.

        Args:
            skill: Skill entity to add
            prerequisites: List of prerequisite skill IDs

        Raises:
            ValueError: If skill already exists, prerequisite is unknown,
                    or graph becomes cyclic after insertion
        """
        if skill.id in self.skills:
            raise ValueError(f"Duplicate skill with id: {skill.id}")

        prerequisites = prerequisites or []
        for prerequisite in prerequisites:
            if prerequisite not in self.skills:
                raise ValueError(f"Unknown prerequisite: {prerequisite} for {skill.id}")

        self.skills[skill.id] = skill

        for prerequisite in prerequisites:
            self.prerequisites_map[skill.id].add(prerequisite)
            self.dependents_map[prerequisite].add(skill.id)

        self.validate_no_cycles()
        self.recalculate_depth_cache()

    def recalculate_depth_cache(self):
        """
        Recalculate and store depth for every node in the graph.

        Depth definition:
            - root node (no prerequisites) -> depth 0
            - other node -> 1 + max(depth of its prerequisites)
        """
        ordered = self.topological_sort()
        self.depth_cache = {}

        for skill_id in ordered:
            prerequisites = self.prerequisites_map[skill_id]
            if not prerequisites:
                self.depth_cache[skill_id] = 0
                continue

            self.depth_cache[skill_id] = 1 + max(
                self.depth_cache[prerequisite] for prerequisite in prerequisites
            )

    def get_depth(self, skill_id: str) -> int:
        """
        Get cached node depth.

        Args:
            skill_id: Skill ID

        Returns:
            int: Cached depth value
        """
        if skill_id not in self.skills:
            raise ValueError(f"No such skill: {skill_id}")

        if skill_id not in self.depth_cache:
            self.recalculate_depth_cache()

        return self.depth_cache[skill_id]

    def validate_no_cycles(self):
        """
        Check if the graph contains any cycles.
        
        Uses iterative DFS to detect cycles in the directed graph.
        A cycle would make it impossible to determine a valid learning order.
        
        Returns:
            None
        
        Raises:
            ValueError: If a cycle is detected in the graph
        """
        visited = set()

        def dfs(skill_id: str) -> bool:
            stack = [(skill_id, False)]
            path = set()
            
            while stack:
                node, is_backtrack = stack.pop()
                
                if is_backtrack:
                    path.remove(node)
                    continue

                if node in path:
                    return True
                
                if node in visited:
                    continue
                
                visited.add(node)
                path.add(node)

                stack.append((node, True))

                for neighbour in self.dependents_map[node]:
                    stack.append((neighbour, False))
            
            return False
        
        for skill_id in self.skills:
            if skill_id not in visited and dfs(skill_id):
                raise ValueError("Graph contains a cycle!")

    def get_transitive_deps(self, skill_id: str) -> Set[str]:
        """
        Returns all transitive dependencies (prerequisites) of a skill.
        
        Args:
            skill_id: ID of the skill
            
        Returns:
            Set[str]: Set of all prerequisite skill IDs
        """
        if skill_id not in self.skills:
            raise ValueError(f"No such skill: {skill_id}")
        
        deps = set()
        stack = list(self.prerequisites_map[skill_id])
        
        while stack:
            current_id = stack.pop()
            
            if current_id in deps:
                continue
                
            if current_id in self.skills:
                deps.add(current_id)
                stack.extend(self.prerequisites_map[current_id])
        
        return deps

    def subgraph(self, subset: Set[str]) -> "SkillGraph":
        """
        Create an induced subgraph containing only nodes in subset.
        """
        for skill_id in subset:
            if skill_id not in self.skills:
                raise ValueError(f"No such skill: {skill_id}")

        graph = SkillGraph()

        for skill_id in subset:
            graph.skills[skill_id] = self.skills[skill_id]

        for skill_id in subset:
            for prereq in self.prerequisites_map[skill_id]:
                if prereq in subset:
                    graph.prerequisites_map[skill_id].add(prereq)
                    graph.dependents_map[prereq].add(skill_id)

        # Original graph is a DAG; induced subgraph is also a DAG.
        graph.recalculate_depth_cache()
        return graph

    def get_subgraph(
        self,
        targets: list[str],
        mode: LearningMode,
        k: int = 1,
    ) -> "SkillGraph":
        """
        Extract a subgraph for given targets and learning mode.

        Modes:
            - SURFACE: only prerequisites needed to reach targets (+ targets)
            - BALANCED: SURFACE + k-hop undirected neighborhood around SURFACE
            - DEEP: entire graph
        """
        if not targets:
            raise ValueError("Targets cannot be empty")

        for target in targets:
            if target not in self.skills:
                raise ValueError(f"No such skill: {target}")

        if mode == LearningMode.DEEP:
            return self.subgraph(set(self.skills.keys()))

        surface = set()
        for target in targets:
            surface.update(self.get_transitive_deps(target))
            surface.add(target)

        if mode == LearningMode.SURFACE:
            return self.subgraph(surface)

        if mode != LearningMode.BALANCED:
            raise ValueError(f"Unknown learning mode: {mode}")

        if k < 0:
            raise ValueError("k must be >= 0")

        expanded = self._k_hop_neighborhood(surface, k=k)

        # Ensure every included node is learnable by including its prerequisite closure.
        closed = set()
        for skill_id in expanded:
            closed.update(self.get_transitive_deps(skill_id))
            closed.add(skill_id)

        return self.subgraph(closed)

    def _k_hop_neighborhood(self, start: Set[str], k: int) -> Set[str]:
        """
        Undirected k-hop neighborhood around start set.

        Uses prerequisites and dependents as undirected edges.
        """
        if k == 0:
            return set(start)

        visited = set(start)
        queue: deque[tuple[str, int]] = deque((node, 0) for node in start)

        while queue:
            node, dist = queue.popleft()
            if dist >= k:
                continue

            neighbours = set(self.prerequisites_map[node]) | set(self.dependents_map[node])
            for neighbour in neighbours:
                if neighbour in visited:
                    continue
                visited.add(neighbour)
                queue.append((neighbour, dist + 1))

        return visited

    def topological_sort(self) -> list[str]:
        """
        Returns a topological order of all skills in the graph.

        Returns:
            list[str]: Skill IDs in valid learning order
        """
        return self._topological_sort_subset(set(self.skills.keys()))

    def topological_sort_for_skill(self, skill_id: str) -> list[str]:
        """
        Returns a topological order for a target skill and all its prerequisites.

        Args:
            skill_id: Target skill ID

        Returns:
            list[str]: Skill IDs required to reach target skill
        """
        if skill_id not in self.skills:
            raise ValueError(f"No such skill: {skill_id}")

        subset = self.get_transitive_deps(skill_id)
        subset.add(skill_id)
        return self._topological_sort_subset(subset)

    def _topological_sort_subset(self, subset: Set[str]) -> list[str]:
        in_degree = {skill_id: 0 for skill_id in self.skills}

        for skill_id, prerequisites in self.prerequisites_map.items():
            if skill_id in self.skills:
                in_degree[skill_id] += len(prerequisites)

        # Heap gives deterministic order between independent nodes.
        zero_degree = [skill_id for skill_id in subset if in_degree[skill_id] == 0]
        heapq.heapify(zero_degree)

        ordered = []
        visited = set()

        while zero_degree:
            current = heapq.heappop(zero_degree)
            if current in visited:
                continue

            visited.add(current)
            ordered.append(current)

            for dependent in self.dependents_map[current]:
                if dependent not in subset:
                    continue
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    heapq.heappush(zero_degree, dependent)

        if len(ordered) != len(subset):
            raise ValueError("Graph contains a cycle!")

        return ordered
