from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.enums import MemberStatus
from app.database import get_db
from app.modules.members import service
from app.modules.members.schemas import MemberCreate, MemberOut, MemberUpdate

router = APIRouter(prefix="/api/members", tags=["members"])


@router.get("", response_model=list[MemberOut])
def list_members(status: MemberStatus | None = None, db: Session = Depends(get_db)):
    return service.list_members(db, status=status)


@router.post("", response_model=MemberOut, status_code=201)
def create_member(payload: MemberCreate, db: Session = Depends(get_db)):
    return service.create_member(db, payload)


@router.get("/{member_id}", response_model=MemberOut)
def get_member(member_id: str, db: Session = Depends(get_db)):
    return service.get_member(db, member_id)


@router.patch("/{member_id}", response_model=MemberOut)
def update_member(member_id: str, payload: MemberUpdate, db: Session = Depends(get_db)):
    return service.update_member(db, member_id, payload)
