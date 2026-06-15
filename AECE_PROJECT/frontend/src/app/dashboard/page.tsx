"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { BarChart, Bar, ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from "recharts";
import * as THREE from "three";
import { useAECEWebSocket, type WsEvent } from "@/lib/ws";
import {
  evaluateAction,
  generateScenario,
  sendFeedback,
  type DecisionType,
  type EvaluateActionRequest,
  type EvaluateActionResponse,
  type Weights,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const SAMPLE_SCENARIO = "Robot must choose between saving 1 person or 5 people";

function DecisionBadge({ score, decision }: { score: number; decision: DecisionType }) {
  const variant =
    score < 20 ? "danger" : score < 50 ? "warning" : score < 80 ? "default" : "success";
  return <Badge variant={variant as any}>{decision}</Badge>;
}

function WeightSlider({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  const pct = Math.round(value * 100) / 100;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm text-zinc-700">{label}</span>
        <span className="font-mono text-sm text-zinc-900">{pct}</span>
      </div>
      <input
        type="range"
        min={0}
        max={1}
        step={0.01}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-cyan-300"
      />
    </div>
  );
}

function FrameworkCharts({ framework_scores }: { framework_scores: EvaluateActionResponse["framework_scores"] }) {
  const barData = [
    { name: "Utilitarian", value: framework_scores.utilitarian },
    { name: "Deontological", value: framework_scores.deontological },
    { name: "Virtue", value: framework_scores.virtue },
    { name: "Care", value: framework_scores.care },
    { name: "Context", value: framework_scores.context },
  ];

  const radarData = [
    { framework: "Utilitarian", score: framework_scores.utilitarian },
    { framework: "Deontological", score: framework_scores.deontological },
    { framework: "Virtue", score: framework_scores.virtue },
    { framework: "Care", score: framework_scores.care },
    { framework: "Context", score: framework_scores.context },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card className="bg-white/70">
        <CardHeader>
          <CardTitle>Ethical Framework Scores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <Bar dataKey="value" fill="rgba(6,182,212,0.8)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-white/70">
        <CardHeader>
          <CardTitle>Framework Radar</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                <PolarGrid stroke="rgba(0,0,0,0.12)" />
                <PolarAngleAxis dataKey="framework" />
                <PolarRadiusAxis domain={[0, 100]} />
                <Radar dataKey="score" stroke="rgba(168,85,247,0.9)" fill="rgba(168,85,247,0.15)" />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function HoloBackdrop() {
  // Three.js background: rotating wireframe ring + particle glow.
  useEffect(() => {
    const mount = document.getElementById("aece-three-mount");
    if (!mount) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    const w = mount.clientWidth;
    const h = mount.clientHeight;
    renderer.setSize(w, h);
    mount.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(55, w / h, 0.1, 1000);
    camera.position.set(0, 0, 3.5);

    const ringGeo = new THREE.TorusGeometry(1.3, 0.05, 24, 120);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x22d3ee, wireframe: true, transparent: true, opacity: 0.8 });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    scene.add(ring);

    const lightGeo = new THREE.BufferGeometry();
    const points: number[] = [];
    for (let i = 0; i < 900; i++) {
      const r = 1.6 * Math.random();
      const theta = Math.random() * Math.PI * 2;
      const y = (Math.random() - 0.5) * 2.4;
      points.push(Math.cos(theta) * r, y, Math.sin(theta) * r);
    }
    lightGeo.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
    const particles = new THREE.Points(
      lightGeo,
      new THREE.PointsMaterial({ color: 0xa855f7, size: 0.02, transparent: true, opacity: 0.7 })
    );
    scene.add(particles);

    let raf = 0;
    const tick = (t: number) => {
      raf = requestAnimationFrame(tick);
      ring.rotation.x = t * 0.00035;
      ring.rotation.y = t * 0.00055;
      particles.rotation.y = t * 0.00012;
      renderer.render(scene, camera);
    };
    raf = requestAnimationFrame(tick);

    const onResize = () => {
      const w2 = mount.clientWidth;
      const h2 = mount.clientHeight;
      renderer.setSize(w2, h2);
      camera.aspect = w2 / h2;
      camera.updateProjectionMatrix();
    };
    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
      cancelAnimationFrame(raf);
      renderer.dispose();
      mount.innerHTML = "";
    };
  }, []);

  return (
    <div
      id="aece-three-mount"
      className="pointer-events-none absolute inset-0 -z-10 overflow-hidden"
    />
  );
}

export default function DashboardPage() {
  const defaultWeights: Weights = useMemo(
    () => ({ w1: 0.22, w2: 0.22, w3: 0.18, w4: 0.18, w5: 0.2 }),
    []
  );

  const [scenario, setScenario] = useState(SAMPLE_SCENARIO);
  const [topic, setTopic] = useState("robot must choose between saving 1 person or 5 people");
  const [style, setStyle] = useState("robot autonomy");
  const [weights, setWeights] = useState<Weights>(defaultWeights);
  const [override, setOverride] = useState<DecisionType | "">("");
  const [policy, setPolicy] = useState<{ require_human_oversight: boolean }>({
    require_human_oversight: true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EvaluateActionResponse | null>(null);

  const [lastFeedback, setLastFeedback] = useState<"approve" | "reject" | null>(null);

  const [systemStatus, setSystemStatus] = useState<any>(null);

  const { connected, send, setWeights: wsSetWeights } = useAECEWebSocket((event: WsEvent) => {
    if (event.type === "system_status") {
      setSystemStatus(event.payload);
    }
    if (event.type === "decision_update") {
      setResult(event.payload?.payload as EvaluateActionResponse);
    }
    if (event.type === "feedback_update") {
      setLastFeedback(event.payload?.user_feedback ?? null);
    }
  });

  async function onEvaluate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLastFeedback(null);

    const trimmed = scenario.trim();
    if (!trimmed) {
      setError("Please enter a scenario.");
      return;
    }

    const payload: EvaluateActionRequest = {
      scenario: trimmed,
      weights,
      governance_override: override ? (override as DecisionType) : null,
      policy_settings: policy,
    };

    setLoading(true);
    try {
      const res = await evaluateAction(payload);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to evaluate scenario.");
    } finally {
      setLoading(false);
    }
  }

  async function onGenerate() {
    setError(null);
    setLoading(true);
    try {
      const res = await generateScenario({ topic, style });
      setScenario(res.scenario);
      if (res.recommended_weights) setWeights(res.recommended_weights);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate scenario.");
    } finally {
      setLoading(false);
    }
  }

  async function onSubmitFeedback(user_feedback: "approve" | "reject") {
    if (!result) return;
    setError(null);
    try {
      await sendFeedback({ decision_id: result.decision_id, user_feedback });
      setLastFeedback(user_feedback);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to store feedback.");
    }
  }

  function scoreTone(score: number) {
    if (score < 20) return "text-red-800 bg-red-50 border-red-200";
    if (score < 50) return "text-amber-900 bg-amber-50 border-amber-200";
    if (score < 80) return "text-zinc-900 bg-zinc-50 border-zinc-200";
    return "text-emerald-900 bg-emerald-50 border-emerald-200";
  }

  return (
    <div className="relative mx-auto w-full max-w-6xl px-6 py-8">
      <HoloBackdrop />

      <div className="relative">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between"
        >
          <div>
            <div className="text-xs text-cyan-200 font-mono tracking-wider">AECE / live console</div>
            <h1 className="text-2xl font-semibold text-black mt-1">Autonomous Ethical Cognition Engine</h1>
            <p className="text-zinc-600 mt-1">
              Jarvis-style real-time ethical scoring for autonomous decision systems.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Badge variant={connected ? "success" : "warning"}>{connected ? "WS Connected" : "WS Offline"}</Badge>
            <Badge variant="default">{systemStatus ? `DB: ${systemStatus.database_connected ? "OK" : "Fail"}` : "System warming up..."}</Badge>
          </div>
        </motion.div>

        <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card className="bg-white/70 backdrop-blur border-black/10">
            <CardHeader>
              <CardTitle>Scenario Input</CardTitle>
              <p className="text-sm text-zinc-600 mt-1">Submit a robot ethical scenario and receive live reasoning.</p>
            </CardHeader>
            <CardContent>
              <form onSubmit={onEvaluate} className="space-y-4">
                <label className="block text-sm font-medium text-zinc-700">Scenario</label>
                <textarea
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                  className="w-full min-h-36 rounded-xl border border-black/10 p-3 outline-none focus:ring-2 focus:ring-cyan-400/30 bg-white/60"
                />

                <div className="flex flex-wrap gap-3 items-center">
                  <Button type="submit" disabled={loading} className="bg-black text-white hover:opacity-90">
                    {loading ? "Evaluating..." : "Evaluate Action"}
                  </Button>
                  <Button type="button" variant="outline" disabled={loading} onClick={() => setScenario("")}>
                    Clear
                  </Button>
                </div>

                {error ? <div className="text-sm text-red-800 bg-red-50 border border-red-200 rounded-xl p-3">{error}</div> : null}
              </form>

              <div className="mt-6 border-t border-black/5 pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-semibold text-black">AI Scenario Generator</div>
                    <div className="text-xs text-zinc-500 mt-1">Generate fresh ethical benchmarks.</div>
                  </div>
                  <Button type="button" variant="outline" onClick={onGenerate} disabled={loading}>
                    {loading ? "Generating..." : "Generate"}
                  </Button>
                </div>

                <div className="mt-4 space-y-3">
                  <label className="block text-sm font-medium text-zinc-700">Topic</label>
                  <input
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="w-full rounded-xl border border-black/10 p-3 outline-none focus:ring-2 focus:ring-cyan-400/30 bg-white/60"
                  />
                  <label className="block text-sm font-medium text-zinc-700">Style</label>
                  <input
                    value={style}
                    onChange={(e) => setStyle(e.target.value)}
                    className="w-full rounded-xl border border-black/10 p-3 outline-none focus:ring-2 focus:ring-cyan-400/30 bg-white/60"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/70 backdrop-blur border-black/10">
            <CardHeader>
              <CardTitle>Stakeholder Control</CardTitle>
              <p className="text-sm text-zinc-600 mt-1">Adjust weights w1..w5 (Utilitarian→Context) in real-time.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <WeightSlider label="w1 Utilitarian" value={weights.w1} onChange={(v) => setWeights((w) => ({ ...w, w1: v }))} />
                <WeightSlider label="w2 Deontological" value={weights.w2} onChange={(v) => setWeights((w) => ({ ...w, w2: v }))} />
                <WeightSlider label="w3 Virtue" value={weights.w3} onChange={(v) => setWeights((w) => ({ ...w, w3: v }))} />
                <WeightSlider label="w4 Care" value={weights.w4} onChange={(v) => setWeights((w) => ({ ...w, w4: v }))} />
                <WeightSlider label="w5 Context" value={weights.w5} onChange={(v) => setWeights((w) => ({ ...w, w5: v }))} />
              </div>

              <div className="flex items-center gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    wsSetWeights(weights);
                  }}
                  disabled={!connected}
                >
                  Push Weights (WS)
                </Button>
                <div className="text-xs text-zinc-500">
                  Used immediately on next evaluation.
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card className="bg-white/70 backdrop-blur border-black/10">
            <CardHeader>
              <CardTitle>Governance Panel</CardTitle>
              <p className="text-sm text-zinc-600 mt-1">Manual override and policy controls.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-zinc-700">Manual Override</label>
                <select
                  value={override}
                  onChange={(e) => setOverride(e.target.value as any)}
                  className="w-full rounded-xl border border-black/10 p-3 outline-none focus:ring-2 focus:ring-cyan-400/30 bg-white/60"
                >
                  <option value="">Auto (engine decides)</option>
                  <option value="Approved">Approved</option>
                  <option value="Conditional">Conditional</option>
                  <option value="Flagged">Flagged</option>
                  <option value="Blocked">Blocked</option>
                </select>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-black/10 bg-white/50 p-3">
                <div>
                  <div className="text-sm font-semibold text-black">Require Human Oversight</div>
                  <div className="text-xs text-zinc-500 mt-1">Policy hint passed to backend.</div>
                </div>
                <input
                  type="checkbox"
                  checked={policy.require_human_oversight}
                  onChange={(e) => setPolicy({ require_human_oversight: e.target.checked })}
                />
              </div>

              <div className="text-xs text-zinc-500">
                Note: for the demo, governance override directly controls decision output.
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/70 backdrop-blur border-black/10">
            <CardHeader>
              <CardTitle>AI Reasoning + Score</CardTitle>
              <p className="text-sm text-zinc-600 mt-1">Breakdown, rationale, and alternatives.</p>
            </CardHeader>
            <CardContent>
              {!result ? (
                <div className="text-zinc-600 text-sm">
                  Run an evaluation to see the ethical reasoning engine output.
                </div>
              ) : (
                <div className="space-y-4">
                  <div className={`rounded-2xl border p-4 ${scoreTone(result.ethical_score)} border-black/10`}>
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="text-xs text-zinc-500">Ethical Score</div>
                        <div className="text-3xl font-semibold text-black">{result.ethical_score}</div>
                        <div className="text-xs text-zinc-500">0 (worst) to 100 (best)</div>
                      </div>
                      <DecisionBadge score={result.ethical_score} decision={result.decision} />
                    </div>
                  </div>

                  {result.ethical_score < 50 ? (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="rounded-2xl border border-red-200 bg-red-50 p-4 overflow-hidden"
                    >
                      <motion.div
                        animate={{ boxShadow: ["0 0 0px rgba(239,68,68,0)", "0 0 30px rgba(239,68,68,0.35)"] }}
                        transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }}
                        className="text-sm font-semibold text-red-800 flex items-center gap-2"
                      >
                        <span className="inline-block w-2 h-2 rounded-full bg-red-500" />
                        Red Alert: Score below 50
                      </motion.div>
                      <div className="text-xs text-red-900/80 mt-2">
                        The decision may violate safety, privacy, fairness, or transparency constraints.
                      </div>
                    </motion.div>
                  ) : null}

                  <FrameworkCharts framework_scores={result.framework_scores} />

                  <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                    <div className="rounded-2xl border border-black/10 bg-white/60 p-4">
                      <div className="text-sm font-semibold text-black">Explanation</div>
                      <p className="mt-2 text-sm text-zinc-700 leading-relaxed">{result.explanation}</p>
                    </div>
                    <div className="rounded-2xl border border-black/10 bg-white/60 p-4">
                      <div className="text-sm font-semibold text-black">Alternative Actions</div>
                      <ul className="mt-2 list-disc pl-5 text-sm text-zinc-700 space-y-1">
                        {result.alternatives.map((a) => (
                          <li key={a}>{a}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-black/10 bg-white/60 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-black">Feedback</div>
                        <div className="text-xs text-zinc-500 mt-1">Approve or reject this decision for continuous learning.</div>
                      </div>
                      {lastFeedback ? <Badge variant={lastFeedback === "approve" ? "success" : "danger"}>{lastFeedback}</Badge> : null}
                    </div>
                    <div className="mt-3 flex gap-3 flex-wrap">
                      <Button type="button" onClick={() => onSubmitFeedback("approve")} disabled={!result}>
                        Approve
                      </Button>
                      <Button type="button" variant="outline" onClick={() => onSubmitFeedback("reject")} disabled={!result}>
                        Reject
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

