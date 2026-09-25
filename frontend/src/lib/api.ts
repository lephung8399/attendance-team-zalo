import type {
  ApiErrorBody,
  MatchSession,
  MatchSessionSummary,
  Member,
  Participant,
  PublishLog,
  PublishPreview,
  PublishResult,
  SkillLevel,
  TeamBoard,
  TeamConfigSuggestion,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  issues: string[];
  status: number;

  constructor(status: number, body: ApiErrorBody) {
    super(body.detail);
    this.status = status;
    this.issues = body.issues ?? [body.detail];
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => ({ detail: res.statusText }))) as ApiErrorBody;
    throw new ApiError(res.status, body);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined });
const patch = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
const del = (path: string) => request<void>(path, { method: "DELETE" });

// Members
export const listMembers = () => get<Member[]>("/api/members");
export const createMember = (data: {
  display_name: string;
  skill_level: SkillLevel;
  nickname?: string;
  note?: string;
}) => post<Member>("/api/members", data);
export const updateMember = (id: string, data: Partial<Member>) =>
  patch<Member>(`/api/members/${id}`, data);

// Sessions
export const listSessions = () => get<MatchSessionSummary[]>("/api/sessions");
export const getSession = (id: string) => get<MatchSession>(`/api/sessions/${id}`);
export const createSession = (data: {
  title: string;
  play_date: string;
  start_time?: string;
  location?: string;
}) => post<MatchSession>("/api/sessions", data);
export const updateSessionConfiguration = (
  id: string,
  data: { team_count: number; player_per_team: number; substitute_count: number },
) => patch<MatchSession>(`/api/sessions/${id}/configuration`, data);
export const getTeamSuggestions = (id: string) =>
  get<TeamConfigSuggestion[]>(`/api/sessions/${id}/team-suggestions`);

// Attendance
export const listParticipants = (sessionId: string) =>
  get<Participant[]>(`/api/sessions/${sessionId}/participants`);
export const syncAttendance = (sessionId: string, memberIds: string[]) =>
  post<Participant[]>(`/api/sessions/${sessionId}/sync-attendance`, { member_ids: memberIds });
export const syncAttendanceFromZalo = (sessionId: string) =>
  post<Participant[]>(`/api/sessions/${sessionId}/sync-attendance/zalo`);
export const addParticipant = (sessionId: string, memberId: string) =>
  post<Participant>(`/api/sessions/${sessionId}/participants`, { member_id: memberId });
export const addGuest = (
  sessionId: string,
  data: { name?: string; skill_level: SkillLevel; referred_by?: string; note?: string },
) => post<Participant>(`/api/sessions/${sessionId}/guests`, data);
export const updateParticipant = (
  sessionId: string,
  participantId: string,
  data: Partial<Pick<Participant, "participant_name" | "skill_level" | "attendance_status" | "note">>,
) => patch<Participant>(`/api/sessions/${sessionId}/participants/${participantId}`, data);
export const removeParticipant = (sessionId: string, participantId: string) =>
  del(`/api/sessions/${sessionId}/participants/${participantId}`);

// Teams / balancing
export const getTeamBoard = (sessionId: string) => get<TeamBoard>(`/api/sessions/${sessionId}/teams`);
export const generateTeams = (sessionId: string, regenerateLocked = false) =>
  post<TeamBoard>(`/api/sessions/${sessionId}/generate-teams`, { regenerate_locked: regenerateLocked });
export const movePlayer = (sessionId: string, participantId: string, targetTeamId: string | null) =>
  post<TeamBoard>(`/api/sessions/${sessionId}/teams/move-player`, {
    participant_id: participantId,
    target_team_id: targetTeamId,
  });
export const swapPlayers = (sessionId: string, a: string, b: string) =>
  post<TeamBoard>(`/api/sessions/${sessionId}/teams/swap`, { participant_id_a: a, participant_id_b: b });
export const toggleLock = (sessionId: string, participantId: string, isLocked: boolean) =>
  post<TeamBoard>(`/api/sessions/${sessionId}/teams/lock`, {
    participant_id: participantId,
    is_locked: isLocked,
  });
export const setTeamColors = (sessionId: string, colors: Record<string, string>) =>
  patch<TeamBoard>(`/api/sessions/${sessionId}/teams/colors`, { colors });
export const finalizeSession = (sessionId: string) => post<MatchSession>(`/api/sessions/${sessionId}/finalize`);
export const reopenSession = (sessionId: string) => post<MatchSession>(`/api/sessions/${sessionId}/reopen`);

// Publishing
export const previewPublish = (sessionId: string) =>
  get<PublishPreview>(`/api/sessions/${sessionId}/publish-preview`);
export const publishSession = (sessionId: string) => post<PublishResult>(`/api/sessions/${sessionId}/publish`);
export const listPublishLogs = (sessionId: string) =>
  get<PublishLog[]>(`/api/sessions/${sessionId}/publish-logs`);
