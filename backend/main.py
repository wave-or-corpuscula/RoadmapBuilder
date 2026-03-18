from fastapi import FastAPI

from backend.api.dependencies import get_graph_repo, get_plan_repo
from backend.api.v1.router import api_router
from backend.domain.skill_graph import SkillGraph
from backend.repositories.graph_repository import InMemoryGraphRepository
from backend.repositories.plan_repository import InMemoryPlanRepository


def create_app(graph: SkillGraph | None = None) -> FastAPI:
    app = FastAPI(title="Adaptive Roadmap Builder")

    graph_repo = InMemoryGraphRepository(graph or SkillGraph())
    plan_repo = InMemoryPlanRepository()

    app.dependency_overrides[get_graph_repo] = lambda: graph_repo
    app.dependency_overrides[get_plan_repo] = lambda: plan_repo

    app.include_router(api_router)
    return app


app = create_app()
