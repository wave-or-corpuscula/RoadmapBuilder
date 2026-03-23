from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.dependencies import (
    get_graph_repo,
    get_knowledge_repo,
    get_plan_repo,
    get_user_repo,
)
from backend.api.v1.router import api_router
from backend.domain.skill_graph import SkillGraph
from backend.repositories.graph_repository import InMemoryGraphRepository
from backend.repositories.knowledge_repository import InMemoryKnowledgeRepository
from backend.repositories.plan_repository import InMemoryPlanRepository
from backend.repositories.user_repository import InMemoryUserRepository


DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def create_app(graph: SkillGraph | None = None) -> FastAPI:
    app = FastAPI(title="Adaptive Roadmap Builder")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEFAULT_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    graph_repo = InMemoryGraphRepository(graph or SkillGraph())
    plan_repo = InMemoryPlanRepository()
    knowledge_repo = InMemoryKnowledgeRepository()
    user_repo = InMemoryUserRepository()

    app.dependency_overrides[get_graph_repo] = lambda: graph_repo
    app.dependency_overrides[get_plan_repo] = lambda: plan_repo
    app.dependency_overrides[get_knowledge_repo] = lambda: knowledge_repo
    app.dependency_overrides[get_user_repo] = lambda: user_repo

    app.include_router(api_router)
    return app


app = create_app()
