"use client";

import { useEffect, useState } from "react";

import { fetchHistory, type DecisionType } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function HistoryPage() {
  const [q, setQ] = useState("");
  const [decision, setDecision] = useState<DecisionType | "">("");
  const [minScore, setMinScore] = useState<number>(0);

  const [limit] = useState<number>(20);
  const [offset, setOffset] = useState<number>(0);

  const [items, setItems] = useState<
    Array<{
      id: string;
      scenario: string;
      ethical_score: number;
      decision: DecisionType;
      explanation: string;
      timestamp: string;
    }>
  >([]);
  const [total, setTotal] = useState<number>(0);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchHistory({
        q: q.trim() ? q.trim() : undefined,
        decision: decision || undefined,
        min_score: minScore || undefined,
        limit,
        offset,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset, limit, q, decision, minScore]);

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-8">
      <div className="flex items-start justify-between gap-6">
        <div>
          <h1 className="text-2xl font-semibold text-black">History</h1>
          <p className="text-zinc-600 mt-1">
            Search and filter stored ethical decisions.
          </p>
        </div>
      </div>

      <Card className="mt-6 bg-white/70 backdrop-blur border-black/10">
        <CardHeader>
          <CardTitle>Search & Filter</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-zinc-700">Query</label>
              <input
                value={q}
                onChange={(e) => {
                  setOffset(0);
                  setQ(e.target.value);
                }}
                placeholder="Search scenario or explanation..."
                className="mt-2 w-full rounded-xl border border-black/10 p-3 outline-none focus:ring-2 focus:ring-cyan-400/30 bg-white/60"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-700">Decision</label>
              <select
                value={decision}
                onChange={(e) => {
                  setOffset(0);
                  setDecision(e.target.value as any);
                }}
                className="mt-2 w-full rounded-xl border border-black/10 p-3 outline-none focus:ring-2 focus:ring-cyan-400/30 bg-white/60"
              >
                <option value="">Any</option>
                <option value="Approved">Approved</option>
                <option value="Conditional">Conditional</option>
                <option value="Flagged">Flagged</option>
                <option value="Blocked">Blocked</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700">
              Min ethical score ({minScore})
            </label>
            <input
              type="range"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => {
                setOffset(0);
                setMinScore(Number(e.target.value));
              }}
              className="w-full mt-2 accent-cyan-300"
            />
          </div>
        </CardContent>
      </Card>

      {error ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-900">
          {error}
        </div>
      ) : null}

      <section className="mt-6 space-y-4">
        {loading ? <div className="text-zinc-600">Loading...</div> : null}
        {!loading && items.length === 0 ? <div className="text-zinc-600">No decisions match.</div> : null}

        {items.map((it) => {
          const variant = it.ethical_score < 20 ? "danger" : it.ethical_score < 50 ? "warning" : "success";
          return (
            <Card key={it.id} className="bg-white/70 backdrop-blur border-black/10">
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-xs text-zinc-500">
                      {new Date(it.timestamp).toLocaleString()}
                    </div>
                    <div className="mt-1 text-sm font-semibold text-black">
                      Ethical score: {it.ethical_score} / 100
                    </div>
                    <div className="mt-2">
                      <Badge variant={variant as any}>{it.decision}</Badge>
                    </div>
                  </div>
                  <div className="text-xs text-zinc-500 font-mono break-all max-w-[220px]">
                    {it.id}
                  </div>
                </div>

                <div className="mt-3 whitespace-pre-wrap text-sm text-zinc-700">
                  {it.scenario}
                </div>
                <div className="mt-2 text-sm text-zinc-600 whitespace-pre-wrap">
                  {it.explanation}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </section>

      <div className="mt-6 flex items-center justify-between">
        <Button
          type="button"
          variant="outline"
          onClick={() => setOffset((o) => Math.max(0, o - limit))}
          disabled={offset === 0 || loading}
        >
          Previous
        </Button>
        <div className="text-sm text-zinc-600">
          Showing {items.length} of {total}
        </div>
        <Button
          type="button"
          onClick={() => setOffset((o) => o + limit)}
          disabled={offset + limit >= total || loading}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

