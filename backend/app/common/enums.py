import enum


class SkillLevel(str, enum.Enum):
    GIOI = "GIOI"
    TRUNG_BINH = "TRUNG_BINH"
    YEU = "YEU"
    UNKNOWN = "UNKNOWN"


class MemberStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class ParticipantType(str, enum.Enum):
    MEMBER = "MEMBER"
    GUEST = "GUEST"


class AttendanceSource(str, enum.Enum):
    ZALO = "ZALO"
    MANUAL = "MANUAL"
    GUEST = "GUEST"


class AttendanceStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    WAITING = "WAITING"
    CANCELLED = "CANCELLED"


class SessionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    LOCKED = "LOCKED"
    TEAM_GENERATED = "TEAM_GENERATED"
    FINALIZED = "FINALIZED"
    PUBLISHED = "PUBLISHED"


class AssignedBy(str, enum.Enum):
    SYSTEM = "SYSTEM"
    ADMIN = "ADMIN"


class PublishStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


SKILL_LEVEL_LABELS = {
    SkillLevel.GIOI: "Giỏi",
    SkillLevel.TRUNG_BINH: "Trung Bình",
    SkillLevel.YEU: "Yếu",
    SkillLevel.UNKNOWN: "Không rõ",
}
