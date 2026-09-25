from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import MemberStatus
from app.common.exceptions import NotFoundError
from app.common.skill import default_score_for
from app.modules.members.models import Member
from app.modules.members.schemas import MemberCreate, MemberUpdate


def list_members(db: Session, *, status: MemberStatus | None = None) -> list[Member]:
    stmt = select(Member).order_by(Member.display_name)
    if status is not None:
        stmt = stmt.where(Member.status == status)
    return list(db.scalars(stmt))


def get_member(db: Session, member_id: str) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError(f"Member {member_id} not found")
    return member


def create_member(db: Session, data: MemberCreate) -> Member:
    skill_score = data.skill_score if data.skill_score is not None else default_score_for(data.skill_level)
    member = Member(
        display_name=data.display_name,
        nickname=data.nickname,
        zalo_user_id=data.zalo_user_id,
        skill_level=data.skill_level,
        skill_score=skill_score,
        preferred_position=data.preferred_position,
        note=data.note,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def update_member(db: Session, member_id: str, data: MemberUpdate) -> Member:
    member = get_member(db, member_id)
    updates = data.model_dump(exclude_unset=True)
    skill_level_changed = "skill_level" in updates and "skill_score" not in updates
    for field, value in updates.items():
        setattr(member, field, value)
    if skill_level_changed:
        member.skill_score = default_score_for(member.skill_level)
    db.commit()
    db.refresh(member)
    return member
