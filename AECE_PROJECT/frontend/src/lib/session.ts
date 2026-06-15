export const AECE_SESSION_KEY = "aece_session_id";

export function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return "anonymous";

  const existing = window.localStorage.getItem(AECE_SESSION_KEY);
  if (existing && existing.length > 0) return existing;

  const id = crypto.randomUUID();
  window.localStorage.setItem(AECE_SESSION_KEY, id);
  return id;
}

