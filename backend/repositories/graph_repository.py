from backend.domain.skill_graph import SkillGraph


class InMemoryGraphRepository:
    def __init__(self, graph: SkillGraph):
        self._graph = graph

    def get(self) -> SkillGraph:
        return self._graph

    def set(self, graph: SkillGraph):
        self._graph = graph
