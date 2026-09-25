"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useMemo, useState } from "react";
import clsx from "clsx";
import { getSession, listParticipants } from "@/lib/api";
import { SESSION_STATUS_LABEL } from "@/lib/types";
import { AttendanceTab } from "@/components/session/AttendanceTab";
import { ConfigTab } from "@/components/session/ConfigTab";
import { TeamBoardTab } from "@/components/session/TeamBoardTab";
import { PublishTab } from "@/components/session/PublishTab";

type TabKey = "attendance" | "config" | "board" | "publish";

const TABS: { key: TabKey; label: string }[] = [
  { key: "attendance", label: "1. Điểm danh" },
  { key: "config", label: "2. Cấu hình đội" },
  { key: "board", label: "3. Chia đội" },
  { key: "publish", label: "4. Công bố" },
];

export default function SessionDetailPage() {
  const params = useParams<{ id: string }>();
  const sessionId = params.id;

  const sessionQuery = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => getSession(sessionId),
  });
  const participantsQuery = useQuery({
    queryKey: ["participants", sessionId],
    queryFn: () => listParticipants(sessionId),
  });

  const defaultTab: TabKey = useMemo(() => {
    const status = sessionQuery.data?.status;
    if (status === "FINALIZED" || status === "PUBLISHED") return "publish";
    if (status === "TEAM_GENERATED") return "board";
    if (status === "LOCKED") return "config";
    return "attendance";
  }, [sessionQuery.data?.status]);

  const [tab, setTab] = useState<TabKey | null>(null);
  const activeTab = tab ?? defaultTab;

  if (sessionQuery.isLoading) {
    return <p className="text-sm text-muted-foreground">Đang tải…</p>;
  }
  if (sessionQuery.isError || !sessionQuery.data) {
    return <p className="text-sm text-danger">Không tìm thấy buổi đá.</p>;
  }

  const session = sessionQuery.data;
  const participantCount = participantsQuery.data?.filter((p) => p.attendance_status !== "CANCELLED").length ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-xs text-muted-foreground">
          <Link href="/" className="hover:underline">
            Tổng quan
          </Link>{" "}
          / Buổi đá
        </p>
        <div className="mt-1 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{session.title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {new Date(session.play_date).toLocaleDateString("vi-VN")}
              {session.start_time ? ` · ${session.start_time.slice(0, 5)}` : ""}
              {session.location ? ` · ${session.location}` : ""} · {participantCount} người tham gia
            </p>
          </div>
          <span className="rounded-full bg-surface-muted px-3 py-1 text-xs font-medium">
            {SESSION_STATUS_LABEL[session.status]}
          </span>
        </div>
      </div>

      <div className="flex gap-1 overflow-x-auto border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={clsx(
              "whitespace-nowrap border-b-2 px-3 py-2.5 text-sm font-medium transition-colors",
              activeTab === t.key
                ? "border-accent text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "attendance" && <AttendanceTab sessionId={sessionId} session={session} />}
      {activeTab === "config" && (
        <ConfigTab sessionId={sessionId} session={session} participantCount={participantCount} />
      )}
      {activeTab === "board" && <TeamBoardTab sessionId={sessionId} session={session} />}
      {activeTab === "publish" && <PublishTab sessionId={sessionId} session={session} />}
    </div>
  );
}
