"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { createSession, listSessions } from "@/lib/api";
import { SESSION_STATUS_LABEL, type SessionStatus } from "@/lib/types";
import { Button, Card, EmptyState, Field, inputClass } from "@/components/ui";

function statusTone(status: SessionStatus) {
  if (status === "PUBLISHED") return "bg-success-bg text-success";
  if (status === "FINALIZED" || status === "TEAM_GENERATED") return "bg-surface-muted text-foreground";
  return "bg-surface-muted text-muted-foreground";
}

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const sessionsQuery = useQuery({ queryKey: ["sessions"], queryFn: listSessions });

  const [form, setForm] = useState({ title: "", play_date: "", start_time: "20:30", location: "" });
  const createMutation = useMutation({
    mutationFn: () =>
      createSession({
        title: form.title,
        play_date: form.play_date,
        start_time: form.start_time ? `${form.start_time}:00` : undefined,
        location: form.location || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      setShowForm(false);
      setForm({ title: "", play_date: "", start_time: "20:30", location: "" });
    },
  });

  const sessions = sessionsQuery.data ?? [];
  const upcoming = sessions.filter((s) => s.status !== "PUBLISHED").slice(0, 1)[0];

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Tổng quan</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Theo dõi các buổi đá, điểm danh và chia đội cân bằng.
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowForm((v) => !v)}>
          + Tạo buổi đá
        </Button>
      </div>

      {showForm && (
        <Card className="p-5">
          <form
            className="grid grid-cols-1 gap-4 sm:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate();
            }}
          >
            <Field label="Tiêu đề">
              <input
                required
                className={inputClass}
                placeholder="Thứ 5 hàng tuần"
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              />
            </Field>
            <Field label="Ngày đá">
              <input
                required
                type="date"
                className={inputClass}
                value={form.play_date}
                onChange={(e) => setForm((f) => ({ ...f, play_date: e.target.value }))}
              />
            </Field>
            <Field label="Giờ đá">
              <input
                type="time"
                className={inputClass}
                value={form.start_time}
                onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
              />
            </Field>
            <Field label="Địa điểm">
              <input
                className={inputClass}
                placeholder="Sân ABC"
                value={form.location}
                onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
              />
            </Field>
            <div className="sm:col-span-2 flex items-center gap-2">
              <Button type="submit" variant="primary" disabled={createMutation.isPending}>
                Tạo buổi đá
              </Button>
              <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>
                Huỷ
              </Button>
            </div>
          </form>
        </Card>
      )}

      {upcoming && (
        <Card className="p-5" style={{ borderColor: "var(--accent)" }}>
          <p className="text-xs font-medium uppercase tracking-wide text-accent">Buổi đá gần nhất</p>
          <div className="mt-2 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">{upcoming.title}</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                {new Date(upcoming.play_date).toLocaleDateString("vi-VN")}
                {upcoming.start_time ? ` · ${upcoming.start_time.slice(0, 5)}` : ""}
                {upcoming.location ? ` · ${upcoming.location}` : ""}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {upcoming.participant_count} người tham gia
              </p>
            </div>
            <Link href={`/sessions/${upcoming.id}`}>
              <Button variant="primary">Quản lý →</Button>
            </Link>
          </div>
        </Card>
      )}

      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Tất cả buổi đá</h2>
        {sessionsQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">Đang tải…</p>
        ) : sessions.length === 0 ? (
          <EmptyState title="Chưa có buổi đá nào" hint="Tạo buổi đá đầu tiên để bắt đầu điểm danh." />
        ) : (
          <div className="flex flex-col gap-2">
            {sessions.map((s) => (
              <Link key={s.id} href={`/sessions/${s.id}`}>
                <Card className="flex items-center justify-between gap-4 p-4 transition-colors hover:border-accent/50">
                  <div>
                    <p className="font-medium">{s.title}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(s.play_date).toLocaleDateString("vi-VN")}
                      {s.location ? ` · ${s.location}` : ""} · {s.participant_count} người
                    </p>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusTone(s.status)}`}>
                    {SESSION_STATUS_LABEL[s.status]}
                  </span>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
