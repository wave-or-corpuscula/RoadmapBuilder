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
    def from_json(cls, path: str) -> "SkillGraph":

        graph = cls()

        with open(path) as file:
            data = json.load(file)
        
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

            graph.skills[skill.id] = skill

        for raw in data["skills"]:
            skill_id = raw["id"]
            for prereq in raw.get("prerequisites", []):
                if prereq not in graph.skills:
                    raise ValueError(f"Unknown prerequisete: {prereq} for {skill_id}")
                
                graph.prerequisites_map[skill_id].add(prereq)
                graph.dependents_map[prereq].add(skill_id)


        graph.validate_no_cycles()

        return graph
    
    def validate_no_cycles(self):
        # TODO: Implement
        ...
