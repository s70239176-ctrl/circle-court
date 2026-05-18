import type React from "react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, TextareaHTMLAttributes } from "react";
import { cn } from "../lib/utils";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-md border border-court-line bg-court-mint px-4 text-sm font-semibold text-court-ink transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  );
}

export function GhostButton({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <Button className={cn("bg-transparent text-slate-100 hover:bg-white/5", className)} {...props} />;
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn("h-10 w-full rounded-md border border-court-line bg-[#10141d] px-3 text-sm outline-none focus:border-court-mint", className)} {...props} />;
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn("min-h-28 w-full rounded-md border border-court-line bg-[#10141d] px-3 py-2 text-sm outline-none focus:border-court-mint", className)} {...props} />;
}

export function Panel({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-lg border border-court-line bg-court-panel p-4 shadow-xl shadow-black/20", className)} {...props} />;
}

export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "good" | "warn" | "bad" }) {
  const tones = {
    neutral: "border-slate-600 text-slate-200",
    good: "border-court-mint text-court-mint",
    warn: "border-court-gold text-court-gold",
    bad: "border-court-coral text-court-coral"
  };
  return <span className={cn("inline-flex rounded border px-2 py-0.5 text-xs font-medium", tones[tone])}>{children}</span>;
}
