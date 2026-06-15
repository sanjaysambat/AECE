"use client";

import { useEffect, useMemo, useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || "http://localhost:8000";

function toWsUrl(httpUrl: string) {
  return httpUrl.replace(/^http:/, "ws:").replace(/^https:/, "wss:");
}

export type WsEvent =
  | { type: "system_status"; payload: any }
  | { type: "decision_update"; payload: any }
  | { type: "feedback_update"; payload: any }
  | { type: "weights_update"; payload: any }
  | { type: string; payload: any };

export function useAECEWebSocket(onEvent?: (event: WsEvent) => void) {
  const wsUrl = useMemo(() => `${toWsUrl(API_URL)}/ws`, []);
  const [connected, setConnected] = useState(false);
  const [wsRef, setWsRef] = useState<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
    } catch {
      setConnected(false);
      return;
    }

    ws.onopen = () => {
      setConnected(true);
      setWsRef(ws);
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (m) => {
      try {
        const data = JSON.parse(m.data);
        if (data?.type) onEvent?.(data as WsEvent);
      } catch {
        // ignore
      }
    };

    return () => {
      ws?.close();
      setWsRef(null);
    };
  }, [wsUrl, onEvent]);

  function send(event: Record<string, any>) {
    if (!wsRef) return;
    wsRef.send(JSON.stringify(event));
  }

  function setWeights(weights: Record<string, any>) {
    send({ type: "set_weights", weights });
  }

  return { connected, wsUrl, send, setWeights };
}

