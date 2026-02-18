import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, Set, List

from app.core.models import Skill


class SkillGraph:

    def __init__(self) -> None:
        self.skills: Dict[str, Skill] = {}
        self.dependents_map: Dict[str, Set[str]] = defaultdict(set)
        self.prerequisites_map: Dict[str, Set[str]] = defaultdict(set)

        self._depth_cache: Dict[str, int] = {}

    def __str__(self) -> str:
        return (f"SkillGraph(skills={len(self.skills)} nodes, "
                f"edges={sum(len(edges) for edges in self.dependents_map.values())} edges)")
    
    def __repr__(self) -> str:
        return (f"<SkillGraph skills={list(self.skills.keys())} "
                f"adj={dict(self.dependents_map)} "
                f"reverse_adj={dict(self.prerequisites_map)}>")

    
    @classmethod
    def from_json(cls, path: str | Path) -> "SkillGraph": # [ ]: Learn Kahn's algorithm
        graph = cls()

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for raw in data["skills"]:
            skill_id = raw["id"]

            if skill_id in graph.skills:
                raise ValueError(f"Duplicate skill id: {skill_id}")
            
            skill = Skill(
                id=skill_id,
                title=raw["title"],
                description=raw["description"],
                difficulty=raw["difficulty"], 
            )

            graph.skills[skill_id] = skill

        for raw in data["skills"]:
            skill_id = raw["id"]
            for prereq in raw.get("prerequisites", []):
                if prereq not in graph.skills:
                    raise ValueError(f"Unknow prerequisite: {prereq} for {skill_id}")
                
                graph.prerequisites_map[skill_id].add(prereq)
                graph.dependents_map[prereq].add(skill_id)

        graph.validate_no_cycles()
        graph._recalculate_depth()
        return graph
    

    def validate_no_cycles(self) -> None:
        indegree = {sid: len(self.prerequisites_map[sid]) for sid in self.skills}

        queue = deque([sid for sid, deg in indegree.items() if deg == 0])
        visited = 0

        while queue:
            node = queue.popleft()
            visited += 1

            for neighbor in self.dependents_map[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if visited != len(self.skills):
            raise ValueError("Graph contains a cycle")
        
    
    def get_prerequisites(self, skill_id: str) -> Set[str]:
        return set(self.prerequisites_map[skill_id])
    
    def get_dependents(self, skill_id: str) -> Set[str]:
        return set(self.dependents_map[skill_id])
    
    def get_transitive_prerequisites(self, skill_id: str) -> Set[str]:
        visited = set()
        stack = [skill_id]

        while stack:
            current = stack.pop()
            for prereq in self.prerequisites_map[current]:
                if prereq not in visited:
                    visited.add(prereq)
                    stack.append(prereq)

        return visited
    
    def topological_sort(self) -> List[str]:
        indegree = {sid: len(self.prerequisites_map[sid]) for sid in self.skills}
        queue = deque([sid for sid, deg in indegree.items() if deg == 0])

        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for neighbor in self.dependents_map[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.skills):
            raise ValueError("Graph contains a cycle")

        return result

    def get_roots(self) -> Set[str]:
        return {sid for sid in self.skills if not self.prerequisites_map[sid]}
    
    def get_leaves(self) -> Set[str]:
        return {sid for sid in self.skills if not self.dependents_map[sid]}

    def add_skill(self, skill: Skill) -> None:
        if skill.id in self.skills:
            raise ValueError(f"Skill {skill.id} already exists")
        self.skills[skill.id] = skill

        self.dependents_map.setdefault(skill.id, set())
        self.prerequisites_map.setdefault(skill.id, set())

        self._recalculate_depth()

    def add_prerequisite(self, skill_id: str, prereq_id: str) -> None:

        if skill_id not in self.skills:
            raise ValueError(f"No such skill: {skill_id}")
        
        if prereq_id not in self.skills:
            raise ValueError(f"No such skill: {prereq_id}")
        
        if skill_id == prereq_id:
            raise ValueError("Skill cannot depend on itself")
        
        if prereq_id in self.prerequisites_map[skill_id]:
            raise ValueError("Prerequisite already exists")
        

        self.prerequisites_map[skill_id].add(prereq_id)
        self.dependents_map[prereq_id].add(skill_id)

        try:
            self.validate_no_cycles()
        except ValueError:
            self.prerequisites_map[skill_id].remove(prereq_id)
            self.dependents_map[prereq_id].remove(skill_id)
            raise
    
    def _recalculate_depth(self) -> None:
        self._depth_cache.clear()

        for node in self.topological_sort():
            prereqs = self.prerequisites_map[node]

            if not prereqs:
                self._depth_cache[node] = 0
            else:
                self._depth_cache[node] = (
                    1 + max(self._depth_cache[pr] for pr in prereqs)
                )

    def calculate_depth(self, skill_id: str) -> int:
        return self._depth_cache[skill_id]
            




