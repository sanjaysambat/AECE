import json
import os
from typing import Any

from shared.schemas import GenerateScenarioRequest, GenerateScenarioResponse, Weights


def _fallback_scenario(req: GenerateScenarioRequest) -> GenerateScenarioResponse:
    topic = req.topic.strip()
    style = req.style or "robot autonomy"

    scenario = (
        f"Robot operating under {style} must choose an action related to '{topic}'. "
        "A poor choice could harm multiple people while a safer option may delay service. "
        "The robot should balance immediate outcomes with long-term safety and consent."
    )

    # Suggest neutral default weights for the UI.
    return GenerateScenarioResponse(scenario=scenario, recommended_weights=Weights())


def _try_call_openai(api_key: str, req: GenerateScenarioRequest) -> GenerateScenarioResponse:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    prompt = (
        "You are generating robot ethics benchmark scenarios. "
        "Create ONE scenario suitable for ethical scoring.\n\n"
        f"Topic: {req.topic}\n"
        f"Style: {req.style}\n\n"
        "Return ONLY valid JSON with keys:\n"
        "{ \"scenario\": <string>, \"recommended_weights\": {\"w1\":...,\"w2\":...,\"w3\":...,\"w4\":...,\"w5\":...} }\n"
    )

    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    text = resp.choices[0].message.content or ""
    data: dict[str, Any] = json.loads(text)
    weights = data.get("recommended_weights") or None

    return GenerateScenarioResponse(
        scenario=str(data["scenario"]),
        recommended_weights=Weights(**weights) if weights else None,
    )


def generate_scenario(req: GenerateScenarioRequest) -> GenerateScenarioResponse:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            return _try_call_openai(api_key, req)
        except Exception:
            pass
    return _fallback_scenario(req)

