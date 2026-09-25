"use client";

import clsx from "clsx";
import { forwardRef } from "react";
import type { ButtonHTMLAttributes, HTMLAttributes } from "react";
import type { SkillLevel } from "@/lib/types";
import { SKILL_LABEL } from "@/lib/types";

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(function Card(
  { className, ...props },
  ref,
) {
  return (
    <div
      ref={ref}
      className={clsx("rounded-[var(--radius-card)] border border-border bg-surface", className)}
      {...props}
    />
  );
});

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

export function Button({
  className,
  variant = "secondary",
  size = "md",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: "sm" | "md" }) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-1.5 rounded-full font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        size === "sm" ? "px-3 py-1.5 text-[13px]" : "px-4 py-2 text-sm",
        variant === "primary" &&
          "bg-accent text-accent-foreground hover:bg-accent-hover",
        variant === "secondary" &&
          "border border-border bg-surface text-foreground hover:bg-surface-muted",
        variant === "ghost" && "text-muted-foreground hover:bg-surface-muted hover:text-foreground",
        variant === "danger" && "border border-danger/30 bg-danger-bg text-danger hover:opacity-80",
        className,
      )}
      {...props}
    />
  );
}

export function SkillBadge({ level }: { level: SkillLevel }) {
  const styles: Record<SkillLevel, string> = {
    GIOI: "bg-success-bg text-success",
    TRUNG_BINH: "bg-surface-muted text-foreground",
    YEU: "bg-danger-bg text-danger",
    UNKNOWN: "bg-surface-muted text-muted-foreground",
  };
  return (
    <span className={clsx("rounded-full px-2 py-0.5 text-xs font-medium", styles[level])}>
      {SKILL_LABEL[level]}
    </span>
  );
}

export function Pill({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={clsx("rounded-full bg-surface-muted px-2.5 py-0.5 text-xs text-muted-foreground", className)}>
      {children}
    </span>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-[var(--radius-card)] border border-dashed border-border py-12 text-center">
      <p className="text-sm font-medium text-foreground">{title}</p>
      {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
    </div>
  );
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}

export const inputClass =
  "w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-accent";
