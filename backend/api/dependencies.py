from backend.repositories.graph_repository import PostgresGraphRepository
from backend.repositories.knowledge_repository import PostgresKnowledgeRepository
from backend.repositories.plan_repository import PostgresPlanRepository
from backend.repositories.user_repository import PostgresUserRepository
from backend.services.auth_service import AuthService
from backend.services.graph_service import GraphService
from backend.services.plan_service import PlanService
from backend.services.progress_service import ProgressService
from backend.services.user_service import UserService


def get_plan_service() -> PlanService:
    return PlanService()


def get_graph_service() -> GraphService:
    return GraphService()


def get_progress_service() -> ProgressService:
    return ProgressService()


def get_user_service() -> UserService:
    return UserService()


def get_auth_service() -> AuthService:
    return AuthService()


def get_graph_repo() -> PostgresGraphRepository:
    raise RuntimeError("Graph repository dependency not configured")


def get_plan_repo() -> PostgresPlanRepository:
    raise RuntimeError("Plan repository dependency not configured")


def get_knowledge_repo() -> PostgresKnowledgeRepository:
    raise RuntimeError("Knowledge repository dependency not configured")


def get_user_repo() -> PostgresUserRepository:
    raise RuntimeError("User repository dependency not configured")
