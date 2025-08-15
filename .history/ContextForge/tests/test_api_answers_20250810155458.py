from app.services.answerer.prompt import build_system_prompt


def test_system_prompt_contains_rules():
    s = build_system_prompt()
    assert "ONLY" in s and "[page" in s

