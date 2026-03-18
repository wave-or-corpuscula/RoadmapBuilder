from dataclasses import dataclass

from backend.domain.skill import Skill
from backend.domain.skill_graph import SkillGraph
from backend.repositories.graph_repository import InMemoryGraphRepository


class GraphValidationError(ValueError):
    pass


class GraphNotFoundError(ValueError):
    pass


class GraphConflictError(ValueError):
    pass


@dataclass(frozen=True)
class SkillDTO:
    id: str
    title: str
    description: str
    difficulty: int
    prerequisites: list[str]


class GraphService:
    def list_skills(self, graph: SkillGraph) -> list[SkillDTO]:
        return [self._to_dto(graph, skill_id) for skill_id in sorted(graph.skills.keys())]

    def get_skill(self, graph: SkillGraph, skill_id: str) -> SkillDTO:
        if skill_id not in graph.skills:
            raise GraphNotFoundError(f"Skill not found: {skill_id}")
        return self._to_dto(graph, skill_id)

    def create_skill(
        self,
        repo: InMemoryGraphRepository,
        skill_id: str,
        title: str,
        description: str,
        difficulty: int,
        prerequisites: list[str],
    ) -> SkillDTO:
        graph = repo.get()
        if skill_id in graph.skills:
            raise GraphConflictError(f"Skill already exists: {skill_id}")

        try:
            graph.add_skill(
                Skill(id=skill_id, title=title, description=description, difficulty=difficulty),
                prerequisites=prerequisites,
            )
        except ValueError as exc:
            raise GraphValidationError(str(exc)) from exc

        return self._to_dto(graph, skill_id)

    def update_skill(
        self,
        repo: InMemoryGraphRepository,
        skill_id: str,
        title: str | None = None,
        description: str | None = None,
        difficulty: int | None = None,
        prerequisites: list[str] | None = None,
    ) -> SkillDTO:
        graph = repo.get()
        if skill_id not in graph.skills:
            raise GraphNotFoundError(f"Skill not found: {skill_id}")

        raw = self.graph_to_payload(graph)
        skills_by_id = {item["id"]: item for item in raw["skills"]}
        target = skills_by_id[skill_id]

        if title is not None:
            target["title"] = title
        if description is not None:
            target["description"] = description
        if difficulty is not None:
            target["difficulty"] = difficulty
        if prerequisites is not None:
            target["prerequisites"] = prerequisites

        try:
            rebuilt = SkillGraph.from_dict(raw)
        except ValueError as exc:
            raise GraphValidationError(str(exc)) from exc

        repo.set(rebuilt)
        return self._to_dto(rebuilt, skill_id)

    def delete_skill(self, repo: InMemoryGraphRepository, skill_id: str, force: bool = False):
        graph = repo.get()
        if skill_id not in graph.skills:
            raise GraphNotFoundError(f"Skill not found: {skill_id}")

        dependents = sorted(graph.dependents_map[skill_id])
        if dependents and not force:
            raise GraphConflictError(f"Skill has dependents: {', '.join(dependents)}")

        raw = self.graph_to_payload(graph)
        raw["skills"] = [item for item in raw["skills"] if item["id"] != skill_id]
        for item in raw["skills"]:
            item["prerequisites"] = [pr for pr in item.get("prerequisites", []) if pr != skill_id]

        try:
            rebuilt = SkillGraph.from_dict(raw)
        except ValueError as exc:
            raise GraphValidationError(str(exc)) from exc

        repo.set(rebuilt)

    def validate_graph_payload(self, payload: dict):
        try:
            SkillGraph.from_dict(payload)
        except ValueError as exc:
            raise GraphValidationError(str(exc)) from exc

    def graph_to_payload(self, graph: SkillGraph) -> dict:
        skills = []
        for skill_id in sorted(graph.skills.keys()):
            skill = graph.skills[skill_id]
            skills.append(
                {
                    "id": skill.id,
                    "title": skill.title,
                    "description": skill.description,
                    "difficulty": skill.difficulty,
                    "prerequisites": sorted(graph.prerequisites_map[skill_id]),
                }
            )
        return {"skills": skills}

    def _to_dto(self, graph: SkillGraph, skill_id: str) -> SkillDTO:
        skill = graph.skills[skill_id]
        return SkillDTO(
            id=skill.id,
            title=skill.title,
            description=skill.description,
            difficulty=skill.difficulty,
            prerequisites=sorted(graph.prerequisites_map[skill_id]),
        )
