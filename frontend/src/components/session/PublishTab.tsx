"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  ApiError,
  finalizeSession,
  getTeamBoard,
  listPublishLogs,
  previewPublish,
  publishSession,
  reopenSession,
} from "@/lib/api";
import type { MatchSession } from "@/lib/types";
import { Button, Card, EmptyState } from "@/components/ui";

export function PublishTab({ sessionId, session }: { sessionId: string; session: MatchSession }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const boardQuery = useQuery({ queryKey: ["board", sessionId], queryFn: () => getTeamBoard(sessionId) });
  const isFinalized = session.status === "FINALIZED" || session.status === "PUBLISHED";

  const previewQuery = useQuery({
    queryKey: ["publish-preview", sessionId, session.status],
    queryFn: () => previewPublish(sessionId),
    enabled: isFinalized,
  });
  const logsQuery = useQuery({
    queryKey: ["publish-logs", sessionId],
    queryFn: () => listPublishLogs(sessionId),
    enabled: isFinalized,
  });

  const invalidateSession = () => {
    queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
    queryClient.invalidateQueries({ queryKey: ["board", sessionId] });
  };

  const finalizeMutation = useMutation({
    mutationFn: () => finalizeSession(sessionId),
    onSuccess: invalidateSession,
    onError: (e) => setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra"),
  });
  const reopenMutation = useMutation({
    mutationFn: () => reopenSession(sessionId),
    onSuccess: invalidateSession,
    onError: (e) => setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra"),
  });
  const publishMutation = useMutation({
    mutationFn: () => publishSession(sessionId),
    onSuccess: () => {
      invalidateSession();
      queryClient.invalidateQueries({ queryKey: ["publish-logs", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["publish-preview", sessionId] });
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra"),
  });

  if (!isFinalized) {
    const board = boardQuery.data;
    return (
      <div className="flex flex-col gap-4">
        {error && <p className="text-sm text-danger">{error}</p>}
        {!board || board.teams.length === 0 ? (
          <EmptyState title="Chưa có đội hình" hint="Hoàn tất tab Chia đội trước khi Finalize." />
        ) : (
          <Card className="p-5">
            <p className="text-sm text-muted-foreground">
              Sẵn sàng chốt {board.teams.length} đội · Balance: {board.balance.label}. Sau khi Finalize, danh
              sách và đội hình sẽ bị khoá cho tới khi Re-open (BR-05).
            </p>
            <div className="mt-4">
              <Button variant="primary" disabled={finalizeMutation.isPending} onClick={() => finalizeMutation.mutate()}>
                Finalize
              </Button>
            </div>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      {error && <p className="text-sm text-danger">{error}</p>}

      <Card className="p-5">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">Nội dung công bố</p>
          <Button variant="ghost" size="sm" onClick={() => reopenMutation.mutate()} disabled={reopenMutation.isPending}>
            Re-open để sửa
          </Button>
        </div>
        <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-surface-muted p-4 font-mono text-sm leading-relaxed">
          {previewQuery.data?.message ?? "Đang tạo nội dung…"}
        </pre>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Button
            variant="secondary"
            onClick={async () => {
              if (previewQuery.data?.message) {
                await navigator.clipboard.writeText(previewQuery.data.message);
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              }
            }}
          >
            {copied ? "Đã copy ✓" : "Copy Message"}
          </Button>
          <Button variant="primary" disabled={publishMutation.isPending} onClick={() => publishMutation.mutate()}>
            {session.status === "PUBLISHED" ? "Publish lại" : "Publish to Zalo"}
          </Button>
          {session.status === "PUBLISHED" && (
            <span className="rounded-full bg-success-bg px-2.5 py-1 text-xs font-medium text-success">
              Đã công bố ✓
            </span>
          )}
        </div>
        {publishMutation.data && !publishMutation.data.success && (
          <p className="mt-3 rounded-lg bg-danger-bg px-3 py-2 text-sm text-danger">
            {publishMutation.data.error} — dùng Copy Message ở trên để đăng thủ công, hoặc Publish lại khi đã
            kết nối Zalo.
          </p>
        )}
      </Card>

      {logsQuery.data && logsQuery.data.length > 0 && (
        <Card className="p-5">
          <p className="mb-2 text-sm font-medium">Lịch sử publish</p>
          <ul className="flex flex-col gap-1.5 text-sm">
            {logsQuery.data.map((log) => (
              <li key={log.id} className="flex items-center gap-2 text-muted-foreground">
                <span className={log.status === "SUCCESS" ? "text-success" : "text-danger"}>
                  {log.status === "SUCCESS" ? "✓" : "✗"}
                </span>
                Lần {log.attempt} · {new Date(log.created_at).toLocaleString("vi-VN")}
                {log.error ? ` · ${log.error}` : ""}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
