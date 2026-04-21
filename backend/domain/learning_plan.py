from dataclasses import dataclass, field
from datetime import datetime, UTC

from backend.domain.enums import KnowledgeStatus
from backend.domain.learning_goal import LearningGoal
from backend.domain.user_knowledge import UserKnowledge


@dataclass(frozen=True)
class LearningPlan:
    id: str | None
    user_id: str
    goal: LearningGoal
    ordered_skill_ids: list[str]
    title: str = "Untitled Plan"
    parent_plan_id: str | None = None
    root_plan_id: str | None = None
    source_skill_id: str | None = None
    fingerprint: str | None = None
    skill_statuses: dict[str, KnowledgeStatus] = field(default_factory=dict)
    skill_notes: dict[str, str] = field(default_factory=dict)
    graph_payload: dict | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True

    def __post_init__(self):
        statuses = dict(self.skill_statuses)
        for skill_id in self.ordered_skill_ids:
            statuses[skill_id] = self.skill_statuses.get(skill_id, KnowledgeStatus.UNKNOWN)
        object.__setattr__(self, "skill_statuses", statuses)

        notes = dict(self.skill_notes)
        object.__setattr__(self, "skill_notes", notes)

    def contains(self, skill_id: str) -> bool:
        return skill_id in self.ordered_skill_ids

    def get_status(self, skill_id: str) -> KnowledgeStatus:
        if skill_id not in self.skill_statuses:
            raise ValueError(f"Skill is not in plan: {skill_id}")
        return self.skill_statuses[skill_id]

    def with_skill_status(self, skill_id: str, status: KnowledgeStatus) -> "LearningPlan":
        graph_skill_ids = set()
        if self.graph_payload is not None:
            graph_skill_ids = {item["id"] for item in self.graph_payload.get("skills", [])}

        if skill_id not in self.skill_statuses and skill_id not in graph_skill_ids:
            raise ValueError(f"Skill is not in plan: {skill_id}")

        updated = dict(self.skill_statuses)
        updated[skill_id] = status
        return LearningPlan(
            id=self.id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            title=self.title,
            parent_plan_id=self.parent_plan_id,
            root_plan_id=self.root_plan_id,
            source_skill_id=self.source_skill_id,
            fingerprint=self.fingerprint,
            skill_statuses=updated,
            skill_notes=dict(self.skill_notes),
            graph_payload=self.graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )

    def with_skill_note(self, skill_id: str, note: str) -> "LearningPlan":
        graph_skill_ids = set()
        if self.graph_payload is not None:
            graph_skill_ids = {item["id"] for item in self.graph_payload.get("skills", [])}

        if skill_id not in self.skill_statuses and skill_id not in graph_skill_ids:
            raise ValueError(f"Skill is not in plan: {skill_id}")

        updated_notes = dict(self.skill_notes)
        updated_notes[skill_id] = note
        return LearningPlan(
            id=self.id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            title=self.title,
            parent_plan_id=self.parent_plan_id,
            root_plan_id=self.root_plan_id,
            source_skill_id=self.source_skill_id,
            fingerprint=self.fingerprint,
            skill_statuses=dict(self.skill_statuses),
            skill_notes=updated_notes,
            graph_payload=self.graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )

    def next_unmastered(self, knowledge: UserKnowledge) -> str | None:
        for skill_id in self.ordered_skill_ids:
            if not knowledge.is_mastered(skill_id):
                return skill_id
        return None

    def with_id(self, plan_id: str) -> "LearningPlan":
        return LearningPlan(
            id=plan_id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            title=self.title,
            parent_plan_id=self.parent_plan_id,
            root_plan_id=self.root_plan_id,
            source_skill_id=self.source_skill_id,
            fingerprint=self.fingerprint,
            skill_statuses=dict(self.skill_statuses),
            skill_notes=dict(self.skill_notes),
            graph_payload=self.graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )

    def with_graph_payload(self, graph_payload: dict) -> "LearningPlan":
        return LearningPlan(
            id=self.id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            title=self.title,
            parent_plan_id=self.parent_plan_id,
            root_plan_id=self.root_plan_id,
            source_skill_id=self.source_skill_id,
            fingerprint=self.fingerprint,
            skill_statuses=dict(self.skill_statuses),
            skill_notes=dict(self.skill_notes),
            graph_payload=graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )

    def with_title(self, title: str) -> "LearningPlan":
        normalized_title = title.strip() or "Untitled Plan"
        return LearningPlan(
            id=self.id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            title=normalized_title,
            parent_plan_id=self.parent_plan_id,
            root_plan_id=self.root_plan_id,
            source_skill_id=self.source_skill_id,
            fingerprint=self.fingerprint,
            skill_statuses=dict(self.skill_statuses),
            skill_notes=dict(self.skill_notes),
            graph_payload=self.graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )

    def with_fingerprint(self, fingerprint: str) -> "LearningPlan":
        return LearningPlan(
            id=self.id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            title=self.title,
            parent_plan_id=self.parent_plan_id,
            root_plan_id=self.root_plan_id,
            source_skill_id=self.source_skill_id,
            fingerprint=fingerprint,
            skill_statuses=dict(self.skill_statuses),
            skill_notes=dict(self.skill_notes),
            graph_payload=self.graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )

    def with_skill_notes(self, skill_notes: dict[str, str]) -> "LearningPlan":
        return LearningPlan(
            id=self.id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            title=self.title,
            parent_plan_id=self.parent_plan_id,
            root_plan_id=self.root_plan_id,
            source_skill_id=self.source_skill_id,
            fingerprint=self.fingerprint,
            skill_statuses=dict(self.skill_statuses),
            skill_notes=dict(skill_notes),
            graph_payload=self.graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )

    def with_hierarchy(
        self,
        *,
        parent_plan_id: str | None,
        root_plan_id: str | None,
        source_skill_id: str | None,
    ) -> "LearningPlan":
        return LearningPlan(
            id=self.id,
            user_id=self.user_id,
            goal=self.goal,
            ordered_skill_ids=self.ordered_skill_ids,
            title=self.title,
            parent_plan_id=parent_plan_id,
            root_plan_id=root_plan_id,
            source_skill_id=source_skill_id,
            fingerprint=self.fingerprint,
            skill_statuses=dict(self.skill_statuses),
            skill_notes=dict(self.skill_notes),
            graph_payload=self.graph_payload,
            created_at=self.created_at,
            is_active=self.is_active,
        )
