import json
from typing import Dict, Set
from collections import defaultdict

from .skill import Skill


class SkillGraph:
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.dependents_map: Dict[str, Set[str]] = defaultdict(set)
        self.prerequisites_map: Dict[str, Set[str]] = defaultdict(set)

    @classmethod
    def from_dict(cls, data: dict) -> "SkillGraph":

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
                    raise ValueError(f"Unknown prerequisete: {prereq} for {skill_id}")
                
                graph.prerequisites_map[skill_id].add(prereq)
                graph.dependents_map[prereq].add(skill_id)


        graph.validate_no_cycles()

        return graph


    @classmethod
    def from_json(cls, path: str) -> "SkillGraph":

        with open(path) as file:
            data = json.load(file)

        return SkillGraph.from_dict(data)
        
    
    def validate_no_cycles(self):

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