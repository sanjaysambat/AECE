import os

from app.config import get_settings
from app.services.ethical_scoring import heuristic_assessment
from app.services.llm import score_with_openai


def assess_scenario(scenario: str) -> dict:
    settings = get_settings()

    api_key = settings.openai_api_key or ""
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()

    # Optional LLM usage: if missing credentials, fall back to the heuristic scorer.
    if api_key:
        try:
            result = score_with_openai(scenario)
            # Ensure callers always have model context.
            result.setdefault("model_used", settings.llm_model)
            return result
        except Exception:
            # Never fail the user flow due to LLM parsing/runtime issues.
            result = heuristic_assessment(scenario)
            result["model_used"] = "heuristic"
            return result

    result = heuristic_assessment(scenario)
    result["model_used"] = "heuristic"
    return result

