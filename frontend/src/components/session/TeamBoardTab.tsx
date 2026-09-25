"use client";

import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  ApiError,
  generateTeams,
  getTeamBoard,
  movePlayer,
  setTeamColors,
  swapPlayers,
  toggleLock,
} from "@/lib/api";
import type { MatchSession, Participant, Team } from "@/lib/types";
import { TEAM_COLOR_LABEL, TEAM_COLOR_SWATCH } from "@/lib/types";
import { Button, Card, EmptyState } from "@/components/ui";

const RESERVE_ID = "reserve";
const teamDroppableId = (teamId: string) => `team:${teamId}`;

export function TeamBoardTab({ sessionId, session }: { sessionId: string; session: MatchSession }) {
  const queryClient = useQueryClient();
  const editable = session.status !== "FINALIZED" && session.status !== "PUBLISHED";
  const boardQuery = useQuery({ queryKey: ["board", sessionId], queryFn: () => getTeamBoard(sessionId) });

  const [error, setError] = useState<string | null>(null);
  const [swapSelection, setSwapSelection] = useState<string[]>([]);
  const [activeDrag, setActiveDrag] = useState<Participant | null>(null);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["board", sessionId] });
    queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
  };

  const onErr = (e: unknown) => setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");

  const generateMutation = useMutation({
    mutationFn: (regenerateLocked: boolean) => generateTeams(sessionId, regenerateLocked),
    onSuccess: () => {
      setError(null);
      invalidate();
    },
    onError: onErr,
  });
  const moveMutation = useMutation({
    mutationFn: ({ participantId, targetTeamId }: { participantId: string; targetTeamId: string | null }) =>
      movePlayer(sessionId, participantId, targetTeamId),
    onSuccess: invalidate,
    onError: onErr,
  });
  const swapMutation = useMutation({
    mutationFn: ({ a, b }: { a: string; b: string }) => swapPlayers(sessionId, a, b),
    onSuccess: () => {
      invalidate();
      setSwapSelection([]);
    },
    onError: onErr,
  });
  const lockMutation = useMutation({
    mutationFn: ({ id, locked }: { id: string; locked: boolean }) => toggleLock(sessionId, id, locked),
    onSuccess: invalidate,
    onError: onErr,
  });
  const colorMutation = useMutation({
    mutationFn: ({ teamId, color }: { teamId: string; color: string }) =>
      setTeamColors(sessionId, { [teamId]: color }),
    onSuccess: invalidate,
    onError: onErr,
  });

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  const board = boardQuery.data;

  function handleDragStart(e: DragStartEvent) {
    const all = [...(board?.teams.flatMap((t) => t.members) ?? []), ...(board?.reserve ?? [])];
    setActiveDrag(all.find((p) => p.id === e.active.id) ?? null);
  }

  function handleDragEnd(e: DragEndEvent) {
    setActiveDrag(null);
    if (!e.over) return;
    const participantId = String(e.active.id);
    const overId = String(e.over.id);
    const targetTeamId = overId === RESERVE_ID ? null : overId.replace("team:", "");
    moveMutation.mutate({ participantId, targetTeamId });
  }

  function handleChipClick(participantId: string) {
    if (!swapMode) return;
    // Compute the next selection as a plain value (not inside the setState
    // updater) so the mutate() side effect below runs exactly once — a
    // functional setState updater can be invoked more than once (e.g. React
    // StrictMode's double-invoke in dev) and must stay pure.
    const next = swapSelection.includes(participantId)
      ? swapSelection.filter((id) => id !== participantId)
      : swapSelection.length === 2
        ? [participantId]
        : [...swapSelection, participantId];
    setSwapSelection(next);
    if (next.length === 2) {
      swapMutation.mutate({ a: next[0], b: next[1] });
    }
  }

  const [swapMode, setSwapMode] = useState(false);

  if (boardQuery.isLoading) return <p className="text-sm text-muted-foreground">Đang tải…</p>;

  if (!session.team_count) {
    return <EmptyState title="Chưa cấu hình đội" hint="Quay lại tab Cấu hình đội trước." />;
  }

  return (
    <div className="flex flex-col gap-5">
      {!editable && (
        <div className="rounded-lg bg-surface-muted px-4 py-2.5 text-sm text-muted-foreground">
          Buổi đá đã Finalize — đội hình đã khoá.
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

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button variant="primary" disabled={!editable || generateMutation.isPending} onClick={() => generateMutation.mutate(false)}>
            {board && board.teams.length > 0 ? "Chia lại (giữ người khoá)" : "Chia đội"}
          </Button>
          {board && board.teams.length > 0 && editable && (
            <Button variant="secondary" disabled={generateMutation.isPending} onClick={() => generateMutation.mutate(true)}>
              Chia lại toàn bộ
            </Button>
          )}
        </div>
        {board && board.teams.length > 0 && editable && (
          <Button
            variant={swapMode ? "primary" : "ghost"}
            size="sm"
            onClick={() => {
              setSwapMode((v) => !v);
              setSwapSelection([]);
            }}
          >
            {swapMode ? `Đang chọn để Swap (${swapSelection.length}/2)` : "Chế độ Swap"}
          </Button>
        )}
      </div>

      {board && board.teams.length > 0 && (
        <Card className="p-4">
          <p className="text-xs font-medium text-muted-foreground">Cân bằng đội hình</p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            {board.teams.map((t) => (
              <span key={t.id} className="text-sm">
                {t.name}: <span className="font-medium">{t.strength_score}</span>
              </span>
            ))}
            <span
              className={`ml-auto rounded-full px-2.5 py-0.5 text-xs font-medium ${
                board.balance.label === "Tốt" ? "bg-success-bg text-success" : "bg-surface-muted text-muted-foreground"
              }`}
            >
              {board.balance.label} · chênh lệch {board.balance.difference}
            </span>
          </div>
        </Card>
      )}

      {!board || board.teams.length === 0 ? (
        <EmptyState title="Chưa chia đội" hint="Bấm “Chia đội” để hệ thống tự động chia cân bằng." />
      ) : (
        <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {board.teams.map((team) => (
              <TeamColumn
                key={team.id}
                team={team}
                editable={editable}
                swapMode={swapMode}
                swapSelection={swapSelection}
                onChipClick={handleChipClick}
                onToggleLock={(id, locked) => lockMutation.mutate({ id, locked })}
                onColorChange={(color) => colorMutation.mutate({ teamId: team.id, color })}
              />
            ))}
          </div>
          <ReserveColumn
            participants={board.reserve}
            editable={editable}
            swapMode={swapMode}
            swapSelection={swapSelection}
            onChipClick={handleChipClick}
            onToggleLock={(id, locked) => lockMutation.mutate({ id, locked })}
          />
          <DragOverlay>{activeDrag ? <Chip participant={activeDrag} editable={false} /> : null}</DragOverlay>
        </DndContext>
      )}
    </div>
  );
}

function TeamColumn({
  team,
  editable,
  swapMode,
  swapSelection,
  onChipClick,
  onToggleLock,
  onColorChange,
}: {
  team: Team;
  editable: boolean;
  swapMode: boolean;
  swapSelection: string[];
  onChipClick: (id: string) => void;
  onToggleLock: (id: string, locked: boolean) => void;
  onColorChange: (color: string) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: teamDroppableId(team.id), disabled: !editable });
  const swatch = TEAM_COLOR_SWATCH[team.color] ?? "#999";

  return (
    <Card
      ref={setNodeRef}
      className={`p-4 transition-colors ${isOver ? "border-accent bg-accent/5" : ""}`}
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full border border-border" style={{ background: swatch }} />
          <span className="font-medium">{team.name}</span>
        </div>
        {editable ? (
          <select
            className="rounded-full border border-border bg-surface px-2 py-0.5 text-xs"
            value={team.color}
            onChange={(e) => onColorChange(e.target.value)}
          >
            {Object.keys(TEAM_COLOR_LABEL).map((c) => (
              <option key={c} value={c}>
                {TEAM_COLOR_LABEL[c]}
              </option>
            ))}
          </select>
        ) : (
          <span className="text-xs text-muted-foreground">{TEAM_COLOR_LABEL[team.color]}</span>
        )}
      </div>
      <p className="mb-2 text-xs text-muted-foreground">
        {team.members.length} người · Strength {team.strength_score}
      </p>
      <div className="flex flex-col gap-1.5">
        {team.members.map((p) => (
          <Chip
            key={p.id}
            participant={p}
            editable={editable}
            selected={swapSelection.includes(p.id)}
            swapMode={swapMode}
            onClick={() => onChipClick(p.id)}
            onToggleLock={(locked) => onToggleLock(p.id, locked)}
          />
        ))}
        {team.members.length === 0 && <p className="text-xs text-muted-foreground">Kéo người vào đây</p>}
      </div>
    </Card>
  );
}

function ReserveColumn({
  participants,
  editable,
  swapMode,
  swapSelection,
  onChipClick,
  onToggleLock,
}: {
  participants: Participant[];
  editable: boolean;
  swapMode: boolean;
  swapSelection: string[];
  onChipClick: (id: string) => void;
  onToggleLock: (id: string, locked: boolean) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: RESERVE_ID, disabled: !editable });
  return (
    <Card ref={setNodeRef} className={`p-4 transition-colors ${isOver ? "border-accent bg-accent/5" : ""}`}>
      <p className="mb-3 font-medium">🔄 Dự bị ({participants.length})</p>
      <div className="flex flex-wrap gap-1.5">
        {participants.map((p) => (
          <Chip
            key={p.id}
            participant={p}
            editable={editable}
            selected={swapSelection.includes(p.id)}
            swapMode={swapMode}
            onClick={() => onChipClick(p.id)}
            onToggleLock={(locked) => onToggleLock(p.id, locked)}
          />
        ))}
        {participants.length === 0 && <p className="text-xs text-muted-foreground">Không có ai dự bị</p>}
      </div>
    </Card>
  );
}

function Chip({
  participant,
  editable,
  selected,
  swapMode,
  onClick,
  onToggleLock,
}: {
  participant: Participant;
  editable: boolean;
  selected?: boolean;
  swapMode?: boolean;
  onClick?: () => void;
  onToggleLock?: (locked: boolean) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: participant.id,
    disabled: !editable || swapMode,
  });
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`, zIndex: 50 }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...(editable && !swapMode ? { ...listeners, ...attributes } : {})}
      onClick={onClick}
      className={`flex items-center justify-between gap-2 rounded-lg border px-2.5 py-1.5 text-sm transition-colors ${
        isDragging ? "opacity-50" : ""
      } ${selected ? "border-accent bg-accent/10" : "border-border bg-surface"} ${
        swapMode ? "cursor-pointer" : editable ? "cursor-grab active:cursor-grabbing" : ""
      }`}
    >
      <span className="truncate">{participant.participant_name}</span>
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        {participant.skill_score}
        {editable && onToggleLock && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onToggleLock(!participant.is_locked);
            }}
            title={participant.is_locked ? "Bỏ khoá" : "Khoá vị trí"}
          >
            {participant.is_locked ? "🔒" : "🔓"}
          </button>
        )}
      </span>
    </div>
  );
}
