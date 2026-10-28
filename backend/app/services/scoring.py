import json

from . import llm


def score_open_answer(question_text: str, answer: str) -> dict:
    raw = llm.score_answer(question_text, answer)
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
    except Exception:
        data = {}
    score = data.get("score")
    if not isinstance(score, (int, float)):
        score = 3.0
    return {
        "score": min(5.0, max(1.0, float(score))),
        "reason": data.get("reason", ""),
        "flags": data.get("flags", []),
    }
