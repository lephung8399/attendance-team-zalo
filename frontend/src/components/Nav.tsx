"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const LINKS = [
  { href: "/", label: "Tổng quan" },
  { href: "/members", label: "Thành viên" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-3.5">
        <Link href="/" className="flex items-center gap-2 text-[15px] font-semibold tracking-tight">
          <span
            className="flex h-7 w-7 items-center justify-center rounded-full text-sm"
            style={{ background: "var(--accent)", color: "var(--accent-foreground)" }}
          >
            ⚽
          </span>
          Điểm danh &amp; Chia đội
        </Link>
        <nav className="flex items-center gap-1">
          {LINKS.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  "rounded-full px-3.5 py-1.5 text-sm transition-colors",
                  active
                    ? "bg-surface-muted text-foreground font-medium"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
