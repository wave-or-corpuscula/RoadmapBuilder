from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.db import init_db, reset_db
from backend.core.config import settings
from backend.api.dependencies import (
    get_graph_repo,
    get_knowledge_repo,
    get_plan_repo,
    get_user_repo,
)
from backend.api.v1.router import api_router
from backend.domain.skill_graph import SkillGraph
from backend.repositories.graph_repository import PostgresGraphRepository
from backend.repositories.knowledge_repository import PostgresKnowledgeRepository
from backend.repositories.plan_repository import PostgresPlanRepository
from backend.repositories.user_repository import PostgresUserRepository


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

    if graph is not None:
        reset_db()
    else:
        init_db()
    startup_graph = graph or SkillGraph()
    if graph is None:
        try:
            startup_graph = SkillGraph.from_json(settings.skills_json_path)
        except Exception:
            startup_graph = SkillGraph()

    graph_repo = PostgresGraphRepository(default_graph=startup_graph)
    plan_repo = PostgresPlanRepository()
    knowledge_repo = PostgresKnowledgeRepository()
    user_repo = PostgresUserRepository()

    app.dependency_overrides[get_graph_repo] = lambda: graph_repo
    app.dependency_overrides[get_plan_repo] = lambda: plan_repo
    app.dependency_overrides[get_knowledge_repo] = lambda: knowledge_repo
    app.dependency_overrides[get_user_repo] = lambda: user_repo

    app.include_router(api_router)
    return app


app = create_app()
