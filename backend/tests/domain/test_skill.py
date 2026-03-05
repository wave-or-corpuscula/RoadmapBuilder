import json

from backend.domain.skill import Skill


def test_skill_creation():

    id = "python"
    title = "Learning Python"
    difficulty = 5
    description = "Some description"

    skill = Skill(id, title, description, difficulty)

    assert skill.id == id
    assert skill.title == title
    assert skill.description == description
    assert skill.difficulty == difficulty


def test_skill_from_dict():
    with open("backend/data.testing/skills.json") as f:
        data = json.load(f)
        raw_skills = data["skills"]
        skills_amount = len(raw_skills)

        skill = raw_skills[3]
        skills = [Skill.from_dict(raw) for raw in raw_skills]
    
    assert Skill.from_dict(skill) in skills
    assert len(skills) == skills_amount

