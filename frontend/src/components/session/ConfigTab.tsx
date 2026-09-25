"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ApiError, getTeamSuggestions, updateSessionConfiguration } from "@/lib/api";
import type { MatchSession } from "@/lib/types";
import { Button, Card, Field, inputClass } from "@/components/ui";

interface Config {
  team_count: number;
  player_per_team: number;
  substitute_count: number;
}

const FALLBACK_CONFIG: Config = { team_count: 2, player_per_team: 7, substitute_count: 0 };

export function ConfigTab({
  sessionId,
  session,
  participantCount,
}: {
  sessionId: string;
  session: MatchSession;
  participantCount: number;
}) {
  const queryClient = useQueryClient();
  const suggestionsQuery = useQuery({
    queryKey: ["team-suggestions", sessionId, participantCount],
    queryFn: () => getTeamSuggestions(sessionId),
    enabled: participantCount > 0,
  });

  const savedConfig: Config | null = session.team_count
    ? {
        team_count: session.team_count,
        player_per_team: session.player_per_team ?? FALLBACK_CONFIG.player_per_team,
        substitute_count: session.substitute_count ?? 0,
      }
    : null;
  const recommended = suggestionsQuery.data?.find((s) => s.recommended) ?? null;

  // `override` is only set once the Admin edits a field or picks a suggestion;
  // until then the effective config falls back to the saved session config,
  // then the recommended suggestion, then a sane default — computed at render
  // time so no effect/setState dance is needed to "apply" a default.
  const [override, setOverride] = useState<Config | null>(null);
  const effective: Config = override ?? savedConfig ?? recommended ?? FALLBACK_CONFIG;

  const total = effective.team_count * effective.player_per_team + effective.substitute_count;
  const diff = participantCount - total;
  const [error, setError] = useState<string | null>(null);

  const saveMutation = useMutation({
    mutationFn: () => updateSessionConfiguration(sessionId, effective),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra"),
  });

  const setField = (field: keyof Config, value: number) => setOverride({ ...effective, [field]: value });

  return (
    <div className="flex flex-col gap-6">
      <Card className="p-5">
        <p className="text-sm text-muted-foreground">
          Tổng số người tham gia: <span className="font-medium text-foreground">{participantCount}</span>
        </p>

        {suggestionsQuery.data && suggestionsQuery.data.length > 0 && (
          <div className="mt-4">
            <p className="mb-2 text-xs font-medium text-muted-foreground">Gợi ý cấu hình</p>
            <div className="flex flex-wrap gap-2">
              {suggestionsQuery.data.map((s, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() =>
                    setOverride({
                      team_count: s.team_count,
                      player_per_team: s.player_per_team,
                      substitute_count: s.substitute_count,
                    })
                  }
                  className={`rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                    effective.team_count === s.team_count &&
                    effective.player_per_team === s.player_per_team &&
                    effective.substitute_count === s.substitute_count
                      ? "border-accent bg-accent/10"
                      : "border-border hover:bg-surface-muted"
                  }`}
                >
                  <span className="font-medium">
                    {s.team_count} đội × {s.player_per_team}
                  </span>
                  <span className="ml-1 text-muted-foreground">+ {s.substitute_count} dự bị</span>
                  {s.recommended && <span className="ml-1.5 text-xs text-accent">★ đề xuất</span>}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Field label="Số đội">
            <input
              type="number"
              min={1}
              className={inputClass}
              value={effective.team_count}
              onChange={(e) => setField("team_count", Number(e.target.value))}
            />
          </Field>
          <Field label="Số người / đội">
            <input
              type="number"
              min={1}
              className={inputClass}
              value={effective.player_per_team}
              onChange={(e) => setField("player_per_team", Number(e.target.value))}
            />
          </Field>
          <Field label="Dự bị">
            <input
              type="number"
              min={0}
              className={inputClass}
              value={effective.substitute_count}
              onChange={(e) => setField("substitute_count", Number(e.target.value))}
            />
          </Field>
        </div>

        <div className="mt-4 rounded-lg bg-surface-muted px-4 py-3 text-sm">
          <p>
            {effective.team_count} × {effective.player_per_team} + {effective.substitute_count} ={" "}
            <span className="font-medium">{total}</span>
          </p>
          {diff === 0 ? (
            <p className="mt-1 text-success">✓ Khớp với {participantCount} người tham gia.</p>
          ) : diff > 0 ? (
            <p className="mt-1 text-danger">⚠ Còn {diff} người chưa được phân bổ.</p>
          ) : (
            <p className="mt-1 text-danger">⚠ Dư {-diff} chỗ so với số người tham gia.</p>
          )}
        </div>

        {error && <p className="mt-3 text-sm text-danger">{error}</p>}

        <div className="mt-4">
          <Button variant="primary" disabled={diff !== 0 || saveMutation.isPending} onClick={() => saveMutation.mutate()}>
            Lưu cấu hình
          </Button>
        </div>
      </Card>
    </div>
  );
}
