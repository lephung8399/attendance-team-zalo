"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  addGuest,
  listMembers,
  listParticipants,
  removeParticipant,
  syncAttendance,
  syncAttendanceFromZalo,
  updateParticipant,
} from "@/lib/api";
import { ApiError } from "@/lib/api";
import { SKILL_LABEL, type MatchSession, type SkillLevel } from "@/lib/types";
import { Button, Card, EmptyState, Field, SkillBadge, inputClass } from "@/components/ui";

const SKILL_OPTIONS: SkillLevel[] = ["GIOI", "TRUNG_BINH", "YEU", "UNKNOWN"];

export function AttendanceTab({ sessionId, session }: { sessionId: string; session: MatchSession }) {
  const queryClient = useQueryClient();
  const editable = session.status !== "FINALIZED" && session.status !== "PUBLISHED";

  const membersQuery = useQuery({ queryKey: ["members"], queryFn: listMembers });
  const participantsQuery = useQuery({
    queryKey: ["participants", sessionId],
    queryFn: () => listParticipants(sessionId),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["participants", sessionId] });
    queryClient.invalidateQueries({ queryKey: ["sessions"] });
  };

  const [error, setError] = useState<string | null>(null);

  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>([]);
  const syncMutation = useMutation({
    mutationFn: () => syncAttendance(sessionId, selectedMemberIds),
    onSuccess: () => {
      invalidate();
      setSelectedMemberIds([]);
    },
  });

  const zaloSyncMutation = useMutation({
    mutationFn: () => syncAttendanceFromZalo(sessionId),
    onSuccess: (added) => {
      invalidate();
      setError(added.length === 0 ? "Không có ai check-in mới trong nhóm Zalo kể từ lần đồng bộ trước." : null);
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra"),
  });

  const [guestName, setGuestName] = useState("");
  const [guestSkill, setGuestSkill] = useState<SkillLevel>("UNKNOWN");
  const addGuestMutation = useMutation({
    mutationFn: () => addGuest(sessionId, { name: guestName || undefined, skill_level: guestSkill }),
    onSuccess: () => {
      invalidate();
      setGuestName("");
      setGuestSkill("UNKNOWN");
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra"),
  });

  const removeMutation = useMutation({
    mutationFn: (participantId: string) => removeParticipant(sessionId, participantId),
    onSuccess: invalidate,
    onError: (e) => setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, skill_level }: { id: string; skill_level: SkillLevel }) =>
      updateParticipant(sessionId, id, { skill_level }),
    onSuccess: invalidate,
  });

  const participants = participantsQuery.data ?? [];
  const participantMemberIds = new Set(participants.map((p) => p.member_id).filter(Boolean));
  const availableMembers = (membersQuery.data ?? []).filter(
    (m) => m.status === "ACTIVE" && !participantMemberIds.has(m.id),
  );

  return (
    <div className="flex flex-col gap-6">
      {!editable && (
        <div className="rounded-lg bg-surface-muted px-4 py-2.5 text-sm text-muted-foreground">
          Buổi đá đã Finalize — danh sách tham gia đã khoá (BR-05). Vào tab Công bố để Re-open nếu cần sửa.
        </div>
      )}
      {error && (
        <button
          type="button"
          className="w-full rounded-lg bg-danger-bg px-4 py-2.5 text-left text-sm text-danger"
          onClick={() => setError(null)}
        >
          {error} <span className="text-xs opacity-70">(bấm để đóng)</span>
        </button>
      )}

      {editable && (
        <Card className="p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-medium">Đồng bộ check-in từ Zalo</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Lấy những ai đã gõ từ khoá check-in (vd &quot;tham gia&quot;) trong group Zalo kể từ lần đồng bộ
                trước. Cần cấu hình <code>ZALO_BOT_TOKEN</code> / <code>ZALO_GROUP_CHAT_ID</code>.
              </p>
            </div>
            <Button variant="secondary" disabled={zaloSyncMutation.isPending} onClick={() => zaloSyncMutation.mutate()}>
              Đồng bộ từ Zalo
            </Button>
          </div>
        </Card>
      )}

      {editable && (
        <Card className="p-5">
          <h3 className="text-sm font-medium">Đồng bộ danh sách vote (thủ công)</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Chọn thành viên đã vote tham gia trên Zalo — thay cho việc đọc poll trực tiếp (xem PoC #68 trong spec).
          </p>
          {availableMembers.length === 0 ? (
            <p className="mt-3 text-sm text-muted-foreground">Tất cả thành viên đang hoạt động đã có trong danh sách.</p>
          ) : (
            <div className="mt-3 flex flex-wrap gap-2">
              {availableMembers.map((m) => {
                const checked = selectedMemberIds.includes(m.id);
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() =>
                      setSelectedMemberIds((ids) =>
                        checked ? ids.filter((id) => id !== m.id) : [...ids, m.id],
                      )
                    }
                    className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                      checked
                        ? "border-accent bg-accent text-accent-foreground"
                        : "border-border bg-surface hover:bg-surface-muted"
                    }`}
                  >
                    {m.display_name}
                  </button>
                );
              })}
            </div>
          )}
          <div className="mt-3">
            <Button
              variant="primary"
              disabled={selectedMemberIds.length === 0 || syncMutation.isPending}
              onClick={() => syncMutation.mutate()}
            >
              Đồng bộ {selectedMemberIds.length > 0 ? `(${selectedMemberIds.length})` : ""}
            </Button>
          </div>
        </Card>
      )}

      {editable && (
        <Card className="p-5">
          <h3 className="text-sm font-medium">+ Thêm khách</h3>
          <div className="mt-3 flex flex-wrap items-end gap-3">
            <div className="min-w-[180px]">
              <Field label="Tên (để trống sẽ tự đặt Guest 01, 02…)">
                <input
                  className={inputClass}
                  value={guestName}
                  onChange={(e) => setGuestName(e.target.value)}
                  placeholder="Khách của Nam"
                />
              </Field>
            </div>
            <div className="w-40">
              <Field label="Trình độ">
                <select
                  className={inputClass}
                  value={guestSkill}
                  onChange={(e) => setGuestSkill(e.target.value as SkillLevel)}
                >
                  {SKILL_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {SKILL_LABEL[s]}
                    </option>
                  ))}
                </select>
              </Field>
            </div>
            <Button variant="secondary" disabled={addGuestMutation.isPending} onClick={() => addGuestMutation.mutate()}>
              + Thêm khách
            </Button>
          </div>
        </Card>
      )}

      <div>
        <h3 className="mb-3 text-sm font-medium text-muted-foreground">
          Danh sách tham gia ({participants.length})
        </h3>
        {participants.length === 0 ? (
          <EmptyState title="Chưa có ai tham gia" hint="Đồng bộ thành viên hoặc thêm khách ở trên." />
        ) : (
          <Card>
            <ul className="divide-y divide-border">
              {participants.map((p) => (
                <li key={p.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{p.participant_name}</span>
                    {p.participant_type === "GUEST" && <span className="text-xs text-muted-foreground">(khách)</span>}
                    {p.note && <span className="text-xs text-muted-foreground">· {p.note}</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    {editable ? (
                      <select
                        className="rounded-full border border-border bg-surface px-2.5 py-1 text-xs"
                        value={p.skill_level}
                        onChange={(e) =>
                          updateMutation.mutate({ id: p.id, skill_level: e.target.value as SkillLevel })
                        }
                      >
                        {SKILL_OPTIONS.map((s) => (
                          <option key={s} value={s}>
                            {SKILL_LABEL[s]}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <SkillBadge level={p.skill_level} />
                    )}
                    {editable && (
                      <button
                        className="text-xs text-muted-foreground underline decoration-dotted hover:text-danger"
                        onClick={() => removeMutation.mutate(p.id)}
                      >
                        Xoá
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </div>
  );
}
