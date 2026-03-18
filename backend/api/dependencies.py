from backend.repositories.graph_repository import InMemoryGraphRepository
from backend.repositories.knowledge_repository import InMemoryKnowledgeRepository
from backend.repositories.plan_repository import InMemoryPlanRepository
from backend.services.graph_service import GraphService
from backend.services.plan_service import PlanService
from backend.services.progress_service import ProgressService


def get_plan_service() -> PlanService:
    return PlanService()


def get_graph_service() -> GraphService:
    return GraphService()


def get_progress_service() -> ProgressService:
    return ProgressService()


def get_graph_repo() -> InMemoryGraphRepository:
    raise RuntimeError("Graph repository dependency not configured")


def get_plan_repo() -> InMemoryPlanRepository:
    raise RuntimeError("Plan repository dependency not configured")


def get_knowledge_repo() -> InMemoryKnowledgeRepository:
    raise RuntimeError("Knowledge repository dependency not configured")
