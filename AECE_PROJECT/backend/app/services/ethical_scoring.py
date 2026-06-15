import re


_HARM_KEYWORDS = [
    r"\bkill\b",
    r"\bpoison\b",
    r"\bbomb\b",
    r"\bweapon\b",
    r"\bshoot\b",
    r"\b-suicide\b",
    r"\bself[- ]harm\b",
]

_PRIVACY_KEYWORDS = [
    r"\bpassword\b",
    r"\bssn\b",
    r"\bsocial security\b",
    r"\bcredit card\b",
    r"\bcard number\b",
    r"\bbank account\b",
]

_FAIRNESS_KEYWORDS = [
    r"\bdon't care about\b.*\bprotected\b",
    r"\bdiscriminat",
    r"\bbiased\b",
    r"\bracist\b",
    r"\bsexist\b",
    r"\bgender\b.*\bpreference",
]

_TRANSPARENCY_KEYWORDS = [
    r"\bdeceiv",
    r"\bmislead",
    r"\bhide",
    r"\bwithout consent\b",
    r"\bcovert",
]


def _contains_any(text: str, patterns: list[str]) -> bool:
    for p in patterns:
        if re.search(p, text, flags=re.IGNORECASE):
            return True
    return False


def heuristic_assessment(scenario: str) -> dict:
    scenario_lc = scenario.lower()

    # Start from a generally-safe baseline and reduce based on detected risk.
    harm_safety = 85
    privacy = 85
    fairness = 85
    transparency = 85

    ethical_flags: list[str] = []
    mitigation: list[str] = []

    if _contains_any(scenario_lc, _HARM_KEYWORDS):
        harm_safety = 15
        ethical_flags.append("Potential direct harm or violence")
        mitigation.append("Refuse harmful instructions and steer toward safe alternatives")

    if _contains_any(scenario_lc, _PRIVACY_KEYWORDS):
        privacy = min(privacy, 25)
        ethical_flags.append("Involves sensitive personal/confidential data")
        mitigation.append("Minimize data, require consent, and avoid collecting secrets")

    if _contains_any(scenario_lc, _FAIRNESS_KEYWORDS):
        fairness = min(fairness, 35)
        ethical_flags.append("Potential discriminatory or manipulative bias")
        mitigation.append("Use fairness-aware logic; monitor outcomes and remove sensitive attributes")

    if _contains_any(scenario_lc, _TRANSPARENCY_KEYWORDS):
        transparency = min(transparency, 40)
        ethical_flags.append("Lack of consent or obscured behavior")
        mitigation.append("Provide clear explanations and obtain explicit user consent")

    # If the scenario looks like it has some ambiguity but not strong red flags,
    # provide generic transparency guidance.
    if not ethical_flags:
        ethical_flags = []
        mitigation.append("Ensure the system explains assumptions and respects user intent")

    rationale_parts: list[str] = []
    rationale_parts.append(
        "Scores were estimated from scenario content using a lightweight heuristic rubric."
    )
    rationale_parts.append(
        f"Harm-safety, privacy, fairness, and transparency were adjusted based on matched risk indicators in the text."
    )
    if ethical_flags:
        rationale_parts.append(
            "Detected concerns were summarized to produce dimension scores and an overall ethical risk estimate."
        )
    else:
        rationale_parts.append("No major risk indicators were detected from the scenario text.")
    rationale = " ".join(rationale_parts).strip()

    overall_score = int(round((harm_safety + privacy + fairness + transparency) / 4))

    return {
        "overall_score": overall_score,
        "dimensions": {
            "harm_safety": harm_safety,
            "privacy": privacy,
            "fairness": fairness,
            "transparency": transparency,
        },
        "ethical_flags": ethical_flags,
        "mitigation": mitigation,
        "rationale": rationale,
    }

