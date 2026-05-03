from dataclasses import dataclass


@dataclass
class Skill:
    id: str
    title: str
    description: str
    difficulty: int
    initial_parts: list[str] | None = None
    parent_skill_id: str | None = None
    is_decomposed: bool = False

    def __repr__(self) -> str:
        return f"Skill(id: {self.id})"
    
    def __str__(self) -> str:
        return f"Skill({self.id})"


    @classmethod
    def from_dict(cls, obj: dict) -> "Skill":
        ins = cls(
            id=obj["id"],
            title=obj["title"],
            description=obj["description"],
            difficulty=obj["difficulty"],
            initial_parts=list(obj.get("initial_parts", [])),
            parent_skill_id=obj.get("parent_skill_id"),
            is_decomposed=bool(obj.get("is_decomposed", False)),
        )

        return ins
