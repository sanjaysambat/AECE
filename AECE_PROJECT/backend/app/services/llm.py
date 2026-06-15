import json
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings


def _build_prompt(scenario: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an ethical reasoning engine. Evaluate the user's scenario and return scores in JSON.\n"
                "Return ONLY valid JSON.\n"
                "Scoring rubric (0-100):\n"
                "- harm_safety: likelihood/severity of harm (higher is safer/less harmful)\n"
                "- privacy: respect for personal data and confidentiality (higher is better)\n"
                "- fairness: absence of discrimination or manipulative bias (higher is fairer)\n"
                "- transparency: clarity, consent, and explainability (higher is more transparent)\n"
                "Also provide:\n"
                "- ethical_flags: short list of concerning aspects (empty list if none)\n"
                "- mitigation: short list of improvements/mitigations\n"
                "- rationale: 3-6 sentences summarizing why the scores were chosen\n"
            ),
        },
        {
            "role": "user",
            "content": (
                "Scenario:\n"
                f"{scenario}\n\n"
                "Return JSON with keys:\n"
                "{\n"
                '  "overall_score": <int 0-100>,\n'
                '  "dimensions": {"harm_safety": <int 0-100>, "privacy": <int 0-100>, "fairness": <int 0-100>, "transparency": <int 0-100>},\n'
                '  "rationale": <string>,\n'
                '  "ethical_flags": <string[]>,\n'
                '  "mitigation": <string[]>\n'
                "}\n"
            ),
        },
    ]


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, max=4))
def score_with_openai(scenario: str) -> dict[str, Any]:
    settings = get_settings()
    import os
    api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    prompt = _build_prompt(scenario)
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=prompt,
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content or ""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("LLM output was not a JSON object.")
    return data
