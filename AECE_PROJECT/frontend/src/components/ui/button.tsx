"use client";

import { forwardRef } from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "ghost" | "outline";
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "default", className = "", ...props },
  ref
) {
  const base =
    "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-400/30 disabled:opacity-60 disabled:cursor-not-allowed";
  const styles =
    variant === "default"
      ? "bg-white/10 text-white hover:opacity-90"
      : variant === "outline"
      ? "border border-white/10 bg-transparent hover:bg-white/5 text-white"
      : "bg-transparent hover:bg-white/5 text-white";

  return <button ref={ref} className={`${base} ${styles} ${className}`} {...props} />;
});

