from dataclasses import dataclass, field


@dataclass
class Skill:
    id: str
    title: str
    description: str
    difficulty: int

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
        )

        return ins
