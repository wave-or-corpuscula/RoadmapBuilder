from backend.domain.skill_graph import SkillGraph
from backend.core.db import SessionLocal
from backend.db_models.models import GraphStateModel

class PostgresGraphRepository:
    _STATE_ID = 1

    def __init__(self, default_graph: SkillGraph | None = None):
        if default_graph is not None:
            with SessionLocal() as session:
                row = session.get(GraphStateModel, self._STATE_ID)
                payload = self._graph_to_payload(default_graph)
                if row is None:
                    row = GraphStateModel(id=self._STATE_ID, payload=payload)
                    session.add(row)
                else:
                    row.payload = payload
                session.commit()

    def get(self) -> SkillGraph:
        with SessionLocal() as session:
            row = session.get(GraphStateModel, self._STATE_ID)
            if row is None:
                empty = SkillGraph()
                row = GraphStateModel(id=self._STATE_ID, payload=self._graph_to_payload(empty))
                session.add(row)
                session.commit()
                return empty
            return SkillGraph.from_dict(row.payload)

    def set(self, graph: SkillGraph):
        with SessionLocal() as session:
            row = session.get(GraphStateModel, self._STATE_ID)
            payload = self._graph_to_payload(graph)
            if row is None:
                row = GraphStateModel(id=self._STATE_ID, payload=payload)
                session.add(row)
            else:
                row.payload = payload
            session.commit()

    def _graph_to_payload(self, graph: SkillGraph) -> dict:
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
