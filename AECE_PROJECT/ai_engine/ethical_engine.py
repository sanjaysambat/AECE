import json
import os
import re
from typing import Any

from shared.schemas import (
    DecisionType,
    EvaluateActionRequest,
    EvaluateActionResponse,
    FrameworkScores,
    Weights,
)


def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def _normalize_weights(weights: Weights) -> Weights:
    total = weights.w1 + weights.w2 + weights.w3 + weights.w4 + weights.w5
    if total <= 0:
        return Weights()
    # Normalize while keeping relative preferences.
    return Weights(
        w1=weights.w1 / total,
        w2=weights.w2 / total,
        w3=weights.w3 / total,
        w4=weights.w4 / total,
        w5=weights.w5 / total,
    )


def _score_to_decision(score: int) -> DecisionType:
    if 80 <= score <= 100:
        return "Approved"
    if 50 <= score <= 79:
        return "Conditional"
    if 20 <= score <= 49:
        return "Flagged"
    return "Blocked"


_TOKEN_KILL = re.compile(r"\b(kill|murder|poison|bomb|weapon|shoot|self[- ]harm|suicide)\b", re.I)
_TOKEN_PRIVACY = re.compile(r"\b(password|ssn|social security|credit card|card number|bank account)\b", re.I)
_TOKEN_DECEPTION = re.compile(r"\b(deceiv|mislead|hide|without consent|covert)\b", re.I)
_TOKEN_DISCRIM = re.compile(r"\b(discriminat|biased|racist|sexist)\b", re.I)
_TOKEN_HARM_RISKY = re.compile(r"\b(injury|harm|danger|unsafe|hazard)\b", re.I)
_TOKEN_HELP = re.compile(r"\b(save|protect|help|care|rescue|treat)\b", re.I)
_TOKEN_RULES = re.compile(r"\b(law|policy|regulat|consent|authorization|authorized)\b", re.I)


def heuristic_framework_scores(scenario: str) -> FrameworkScores:
    s = scenario.strip()
    s_lc = s.lower()

    # Start with a relatively positive score and penalize based on risk signals.
    utilitarian = 78
    deontological = 80
    virtue = 78
    care = 76
    context = 82

    # Utilitarian: reward "help/save" language and penalize direct violence/risk.
    if _TOKEN_HELP.search(s_lc):
        utilitarian = _clamp(utilitarian + 6, 0, 100)
    if _TOKEN_KILL.search(s_lc) or _TOKEN_HARM_RISKY.search(s_lc):
        utilitarian = _clamp(utilitarian - 55, 0, 100)

    # Deontological: consent/authorization and avoiding deception.
    if _TOKEN_DECEPTION.search(s_lc):
        deontological = _clamp(deontological - 35, 0, 100)
    if _TOKEN_PRIVACY.search(s_lc):
        deontological = _clamp(deontological - 45, 0, 100)
    if _TOKEN_RULES.search(s_lc):
        deontological = _clamp(deontological + 8, 0, 100)

    # Virtue ethics: responsibility, honesty, avoidance of harmful character-driven choices.
    if _TOKEN_DISCRIM.search(s_lc):
        virtue = _clamp(virtue - 40, 0, 100)
    if _TOKEN_DECEPTION.search(s_lc):
        virtue = _clamp(virtue - 25, 0, 100)

    # Care ethics: empathy and consideration of persons/groups; violence reduces.
    if _TOKEN_KILL.search(s_lc) or _TOKEN_HARM_RISKY.search(s_lc):
        care = _clamp(care - 45, 0, 100)

    # Context: safety/legal/regulatory framing
    if _TOKEN_RULES.search(s_lc):
        context = _clamp(context + 8, 0, 100)
    if _TOKEN_DISCRIM.search(s_lc) or _TOKEN_PRIVACY.search(s_lc):
        context = _clamp(context - 25, 0, 100)

    return FrameworkScores(
        utilitarian=round(utilitarian, 2),
        deontological=round(deontological, 2),
        virtue=round(virtue, 2),
        care=round(care, 2),
        context=round(context, 2),
    )


def _heuristic_explanation_and_alternatives(
    scenario: str, framework_scores: FrameworkScores
) -> tuple[str, list[str]]:
    flags: list[str] = []
    if _TOKEN_KILL.search(scenario):
        flags.append("direct harm/violence risk detected")
    if _TOKEN_PRIVACY.search(scenario):
        flags.append("sensitive personal data handled")
    if _TOKEN_DECEPTION.search(scenario):
        flags.append("deceptive or consent-violating behavior suggested")
    if _TOKEN_DISCRIM.search(scenario):
        flags.append("potential discriminatory or biased reasoning")

    if flags:
        rationale = (
            "The system scored the scenario using a lightweight rubric across five ethical frameworks. "
            "Penalties were applied for detected risk indicators ({}), resulting in a moderated ethical score. "
            "Overall, the evaluation emphasizes safety, respect for persons, and transparency in action selection."
        ).format(", ".join(flags))
    else:
        rationale = (
            "The system scored the scenario using a lightweight rubric across five ethical frameworks. "
            "No major red-flag indicators were found; the resulting ethical score reflects the most likely "
            "ethical considerations implied by the text."
        )

    alternatives: list[str] = []
    # Provide general alternatives for the demo.
    alternatives.append("Use the least harmful option that preserves safety and proportionality.")
    alternatives.append("Prefer actions that require explicit authorization and respect user consent.")
    alternatives.append("If uncertainty is high, request human oversight or additional context before acting.")

    return rationale, alternatives


def _compute_ethical_score(framework: FrameworkScores, weights: Weights) -> int:
    w = _normalize_weights(weights)
    weighted = (
        w.w1 * framework.utilitarian
        + w.w2 * framework.deontological
        + w.w3 * framework.virtue
        + w.w4 * framework.care
        + w.w5 * framework.context
    )
    score = int(round(weighted))
    return max(0, min(100, score))


def _try_call_openai(api_key: str, scenario: str, weights: Weights) -> dict[str, Any]:
    # Delayed import to keep heuristic fallback lightweight.
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    prompt = (
        "You are an ethical reasoning engine for autonomous systems. "
        "Given a scenario, produce ethical framework scores and actionable alternatives. "
        "Return ONLY valid JSON.\n\n"
        "Scenario:\n"
        f"{scenario}\n\n"
        "Weights (w1..w5) are already chosen by stakeholders and must be reflected in the output rationale. "
        "Scoring rubric: each framework score must be an integer 0-100.\n\n"
        "Return JSON with keys:\n"
        "{\n"
        '  "utilitarian": 0-100,\n'
        '  "deontological": 0-100,\n'
        '  "virtue": 0-100,\n'
        '  "care": 0-100,\n'
        '  "context": 0-100,\n'
        '  "explanation": "3-6 sentences, no chain-of-thought",\n'
        '  "alternatives": ["string", "string", "string"]\n'
        "}\n"
    )

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content or ""
    return json.loads(text)


def _try_call_anthropic(api_key: str, scenario: str, weights: Weights) -> dict[str, Any]:
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)

    system = (
        "You are an ethical reasoning engine for autonomous systems. "
        "Return ONLY valid JSON."
    )
    prompt = (
        f"Scenario:\n{scenario}\n\n"
        "Return JSON with keys: utilitarian,deontological,virtue,care,context,explanation,alternatives."
    )

    # Anthropic JSON mode support varies; we'll request the exact keys and parse.
    msg = client.messages.create(
        model=os.getenv("LLM_MODEL", "claude-3-5-sonnet-latest"),
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
        system=system,
    )
    # Extract the first text block.
    content = msg.content[0].text if msg.content else ""
    if not content:
        content = json.dumps(msg.model_dump(), default=str)
    return json.loads(content)


def evaluate_action(request: EvaluateActionRequest, *, learning_context: dict[str, Any] | None = None) -> EvaluateActionResponse:
    weights = _normalize_weights(request.weights or Weights())
    governance_override = request.governance_override

    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    framework_scores: FrameworkScores | None = None
    explanation: str | None = None
    alternatives: list[str] | None = None

    if openai_key:
        try:
            data = _try_call_openai(openai_key, request.scenario, weights)
            framework_scores = FrameworkScores(
                utilitarian=float(data["utilitarian"]),
                deontological=float(data["deontological"]),
                virtue=float(data["virtue"]),
                care=float(data["care"]),
                context=float(data["context"]),
            )
            explanation = str(data.get("explanation") or "")
            alternatives = list(data.get("alternatives") or [])
        except Exception:
            framework_scores = None
    elif anthropic_key:
        try:
            data = _try_call_anthropic(anthropic_key, request.scenario, weights)
            framework_scores = FrameworkScores(
                utilitarian=float(data["utilitarian"]),
                deontological=float(data["deontological"]),
                virtue=float(data["virtue"]),
                care=float(data["care"]),
                context=float(data["context"]),
            )
            explanation = str(data.get("explanation") or "")
            alternatives = list(data.get("alternatives") or [])
        except Exception:
            framework_scores = None

    if framework_scores is None:
        framework_scores = heuristic_framework_scores(request.scenario)
        explanation, alternatives = _heuristic_explanation_and_alternatives(
            request.scenario, framework_scores
        )

    assert explanation is not None
    assert alternatives is not None

    base_score = _compute_ethical_score(framework_scores, weights)

    # Continuous learning via feedback: slight global strictness adjustment.
    # (We keep it lightweight for the demo; feedback is still stored for audit.)
    reject_rate = float(learning_context.get("reject_rate", 0.0)) if learning_context else 0.0
    strictness = _clamp(1.0 - reject_rate * 0.15, 0.7, 1.0)
    final_score = int(round(_clamp(base_score * strictness, 0, 100)))

    decision = _score_to_decision(final_score)
    if governance_override is not None:
        decision = governance_override

    explanation = explanation.strip()
    if not explanation:
        explanation = (
            "Explanation unavailable from the selected reasoning mode; "
            "fallback rubric was used to estimate ethical considerations."
        )

    return EvaluateActionResponse(
        ethical_score=final_score,
        decision=decision,
        explanation=explanation,
        alternatives=alternatives,
        framework_scores=framework_scores,
        weights_used=weights,
        governance_override_applied=(governance_override is not None),
        timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        decision_id="pending",
    )

