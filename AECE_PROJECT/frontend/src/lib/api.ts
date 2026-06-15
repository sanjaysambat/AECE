export type EthicalDimensions = {
  utilitarian: number;
  deontological: number;
  virtue: number;
  care: number;
  context: number;
};

export type EthicalAssessment = {
  id: string;
  scenario: string;
  overall_score: number;
  dimensions: EthicalDimensions;
  rationale: string;
  ethical_flags: string[];
  mitigation: string[];
  model_used?: string;
  created_at: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || "http://localhost:8000";

export type Weights = {
  w1: number;
  w2: number;
  w3: number;
  w4: number;
  w5: number;
};

export type DecisionType = "Approved" | "Conditional" | "Flagged" | "Blocked";

export type EvaluateActionRequest = {
  scenario: string;
  weights?: Weights;
  governance_override?: DecisionType | null;
  policy_settings?: Record<string, any> | null;
};

export type EvaluateActionResponse = {
  ethical_score: number;
  decision: DecisionType;
  explanation: string;
  alternatives: string[];
  framework_scores: EthicalDimensions;
  weights_used: Weights;
  governance_override_applied: boolean;
  timestamp: string;
  decision_id: string;
};

export async function evaluateAction(payload: EvaluateActionRequest) {
  const res = await fetch(`${API_URL}/evaluate-action`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error: ${res.status} ${text}`.trim());
  }

  return (await res.json()) as EvaluateActionResponse;
}

export async function generateScenario(params: {
  topic: string;
  style?: string | null;
}) {
  const res = await fetch(`${API_URL}/generate-scenario`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error: ${res.status} ${text}`.trim());
  }

  return (await res.json()) as {
    scenario: string;
    recommended_weights?: Weights | null;
  };
}

export async function fetchHistory(params: {
  q?: string;
  decision?: DecisionType | string;
  min_score?: number;
  limit?: number;
  offset?: number;
}) {
  const {
    q,
    decision,
    min_score,
    limit = 50,
    offset = 0,
  } = params || {};

  const qs = new URLSearchParams({
    ...(q ? { q: q } : {}),
    ...(decision ? { decision: decision } : {}),
    ...(min_score !== undefined ? { min_score: String(min_score) } : {}),
    limit: String(limit),
    offset: String(offset),
  });

  const res = await fetch(`${API_URL}/history?${qs.toString()}`, {
    method: "GET",
    headers: { "content-type": "application/json" },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error: ${res.status} ${text}`.trim());
  }

  return (await res.json()) as {
    items: Array<{
      id: string;
      scenario: string;
      ethical_score: number;
      decision: DecisionType;
      explanation: string;
      timestamp: string;
    }>;
    total: number;
  };
}

export async function sendFeedback(payload: {
  decision_id: string;
  user_feedback: "approve" | "reject";
}) {
  const res = await fetch(`${API_URL}/feedback`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error: ${res.status} ${text}`.trim());
  }

  return (await res.json()) as { id: string; decision_id: string; user_feedback: string };
}

export async function getSystemStatus() {
  const res = await fetch(`${API_URL}/system-status`, {
    method: "GET",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error: ${res.status} ${text}`.trim());
  }
  return (await res.json()) as {
    status: "ok";
    timestamp: string;
    database_connected: boolean;
    websocket_clients_connected: number;
    scoring_mode: string;
  };
}

