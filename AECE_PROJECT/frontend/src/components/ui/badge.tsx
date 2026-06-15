"use client";

export function Badge({
  children,
  variant = "default",
}: {
  children: React.ReactNode;
  variant?: "default" | "danger" | "warning" | "success";
}) {
  const cls =
    variant === "danger"
      ? "bg-red-900 text-red-100 border-red-800"
      : variant === "warning"
      ? "bg-amber-900 text-amber-100 border-amber-800"
      : variant === "success"
      ? "bg-emerald-900 text-emerald-100 border-emerald-800"
      : "bg-glass text-muted border-white/10";

  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${cls}`}>
      {children}
    </span>
  );
}

