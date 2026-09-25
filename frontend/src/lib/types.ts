export type SkillLevel = "GIOI" | "TRUNG_BINH" | "YEU" | "UNKNOWN";
export type MemberStatus = "ACTIVE" | "INACTIVE";
export type ParticipantType = "MEMBER" | "GUEST";
export type AttendanceStatus = "CONFIRMED" | "WAITING" | "CANCELLED";
export type SessionStatus =
  | "DRAFT"
  | "OPEN"
  | "LOCKED"
  | "TEAM_GENERATED"
  | "FINALIZED"
  | "PUBLISHED";

export const SKILL_LABEL: Record<SkillLevel, string> = {
  GIOI: "Giỏi",
  TRUNG_BINH: "Trung bình",
  YEU: "Yếu",
  UNKNOWN: "Không rõ",
};

export const SESSION_STATUS_LABEL: Record<SessionStatus, string> = {
  DRAFT: "Nháp",
  OPEN: "Đang mở đăng ký",
  LOCKED: "Đã chốt danh sách",
  TEAM_GENERATED: "Đã chia đội",
  FINALIZED: "Đã chốt đội",
  PUBLISHED: "Đã công bố",
};

export const TEAM_COLOR_LABEL: Record<string, string> = {
  WHITE: "Trắng",
  RED: "Đỏ",
  BLUE: "Xanh dương",
  YELLOW: "Vàng",
  BLACK: "Đen",
  GREEN: "Xanh lá",
};

export const TEAM_COLOR_SWATCH: Record<string, string> = {
  WHITE: "#f5f5f0",
  RED: "#c0392b",
  BLUE: "#2b5fa8",
  YELLOW: "#e0b332",
  BLACK: "#26241f",
  GREEN: "#3f7a4e",
};

export interface Member {
  id: string;
  display_name: string;
  nickname: string | null;
  zalo_user_id: string | null;
  skill_level: SkillLevel;
  skill_score: number;
  preferred_position: string | null;
  status: MemberStatus;
  note: string | null;
  created_at: string;
  updated_at: string;
}

export interface MatchSession {
  id: string;
  title: string;
  play_date: string;
  start_time: string | null;
  location: string | null;
  zalo_group_id: string | null;
  poll_id: string | null;
  status: SessionStatus;
  team_count: number | null;
  player_per_team: number | null;
  substitute_count: number | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface MatchSessionSummary extends MatchSession {
  participant_count: number;
}

export interface Participant {
  id: string;
  session_id: string;
  member_id: string | null;
  participant_name: string;
  participant_type: ParticipantType;
  skill_level: SkillLevel;
  skill_score: number;
  attendance_status: AttendanceStatus;
  is_substitute: boolean;
  is_locked: boolean;
  note: string | null;
}

export interface TeamConfigSuggestion {
  team_count: number;
  player_per_team: number;
  substitute_count: number;
  total: number;
  recommended: boolean;
}

export interface Team {
  id: string;
  session_id: string;
  name: string;
  color: string;
  strength_score: number;
  order: number;
  members: Participant[];
}

export interface BalanceSummary {
  strengths: number[];
  difference: number;
  label: string;
}

export interface TeamBoard {
  teams: Team[];
  reserve: Participant[];
  balance: BalanceSummary;
}

export interface PublishPreview {
  message: string;
}

export interface PublishResult {
  success: boolean;
  message: string;
  error: string | null;
  attempt: number;
  session_status: SessionStatus;
}

export interface PublishLog {
  id: string;
  status: "SUCCESS" | "FAILED";
  error: string | null;
  attempt: number;
  created_at: string;
}

export interface ApiErrorBody {
  detail: string;
  issues?: string[];
}
