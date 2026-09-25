from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.common.enums import AssignedBy, SessionStatus
from app.common.exceptions import NotFoundError, ValidationFailedError
from app.config import get_settings
from app.modules.attendance.models import SessionParticipant
from app.modules.attendance.service import list_participants as list_session_participants
from app.modules.audit import service as audit_service
from app.modules.balancing import engine
from app.modules.matches.models import MatchSession
from app.modules.matches.service import get_session
from app.modules.matches.suggestion import validate_configuration
from app.modules.teams.colors import default_colors_for
from app.modules.teams.models import Team, TeamMember
from app.modules.teams.schemas import BalanceSummary, TeamBoardOut, TeamOut


def _active_participants(db: Session, session_id: str) -> list[SessionParticipant]:
    from app.common.enums import AttendanceStatus

    return [
        p
        for p in list_session_participants(db, session_id)
        if p.attendance_status != AttendanceStatus.CANCELLED
    ]


def _ensure_editable(session_status: SessionStatus) -> None:
    if session_status in (SessionStatus.FINALIZED, SessionStatus.PUBLISHED):
        raise ValidationFailedError(
            "Buổi đá đã Finalize. Vui lòng Re-open Session trước khi chỉnh sửa đội (BR-05)."
        )


def _teams_for_session(db: Session, session_id: str) -> list[Team]:
    return list(db.scalars(select(Team).where(Team.session_id == session_id).order_by(Team.order)))


def _recompute_strength(db: Session, team: Team) -> None:
    members = list(
        db.scalars(
            select(SessionParticipant)
            .join(TeamMember, TeamMember.participant_id == SessionParticipant.id)
            .where(TeamMember.team_id == team.id)
        )
    )
    team.strength_score = sum(p.skill_score for p in members)


def get_board(db: Session, session_id: str) -> TeamBoardOut:
    get_session(db, session_id)  # 404 if missing
    teams = _teams_for_session(db, session_id)
    participants = _active_participants(db, session_id)
    participant_by_id = {p.id: p for p in participants}

    team_members_by_team: dict[str, list[SessionParticipant]] = {t.id: [] for t in teams}
    assigned_ids: set[str] = set()
    if teams:
        rows = db.execute(
            select(TeamMember.team_id, TeamMember.participant_id).where(
                TeamMember.team_id.in_([t.id for t in teams])
            )
        ).all()
        for team_id, participant_id in rows:
            if participant_id in participant_by_id:
                team_members_by_team[team_id].append(participant_by_id[participant_id])
                assigned_ids.add(participant_id)

    reserve = [p for p in participants if p.id not in assigned_ids]

    team_outs = [
        TeamOut(
            id=t.id,
            session_id=t.session_id,
            name=t.name,
            color=t.color,
            strength_score=t.strength_score,
            order=t.order,
            members=team_members_by_team[t.id],
        )
        for t in teams
    ]
    strengths = [t.strength_score for t in team_outs]
    difference = (max(strengths) - min(strengths)) if strengths else 0.0
    balance = BalanceSummary(strengths=strengths, difference=difference, label=engine.balance_label(difference))
    return TeamBoardOut(teams=team_outs, reserve=reserve, balance=balance)


def generate_teams(
    db: Session, session_id: str, *, iterations: int | None = None, regenerate_locked: bool = False
) -> TeamBoardOut:
    session = get_session(db, session_id)
    _ensure_editable(session.status)
    if session.team_count is None or session.player_per_team is None or session.substitute_count is None:
        raise ValidationFailedError("Vui lòng cấu hình số đội / số người / dự bị trước khi chia đội.")

    participants = _active_participants(db, session_id)
    issues = validate_configuration(
        team_count=session.team_count,
        player_per_team=session.player_per_team,
        substitute_count=session.substitute_count,
        participant_count=len(participants),
    )
    if issues:
        raise ValidationFailedError(issues[0], issues)

    existing_teams = _teams_for_session(db, session_id)
    current_team_index: dict[str, int] = {}
    if existing_teams:
        team_index_by_id = {t.id: t.order for t in existing_teams}
        rows = db.execute(
            select(TeamMember.team_id, TeamMember.participant_id).where(
                TeamMember.team_id.in_([t.id for t in existing_teams])
            )
        ).all()
        for team_id, participant_id in rows:
            current_team_index[participant_id] = team_index_by_id[team_id]

    players_input = []
    for p in participants:
        locked_idx = None
        if p.is_locked and not regenerate_locked:
            if p.id in current_team_index:
                locked_idx = current_team_index[p.id]
            elif p.is_substitute:
                locked_idx = engine.RESERVE
        players_input.append(engine.PlayerInput(id=p.id, skill_score=p.skill_score, locked_team_index=locked_idx))

    settings = get_settings()
    result = engine.generate_teams(
        players_input,
        team_count=session.team_count,
        players_per_team=session.player_per_team,
        reserve_count=session.substitute_count,
        iterations=iterations or settings.balancing_iterations,
        tie_tolerance=settings.balancing_tie_tolerance,
    )

    if existing_teams:
        teams = existing_teams
    else:
        colors = default_colors_for(session.team_count)
        letters = "ABCDEFGHIJ"
        teams = [
            Team(session_id=session_id, name=f"Team {letters[i]}", color=colors[i], order=i)
            for i in range(session.team_count)
        ]
        db.add_all(teams)
        db.flush()

    team_ids = [t.id for t in teams]
    db.query(TeamMember).filter(TeamMember.team_id.in_(team_ids)).delete(synchronize_session=False)

    participant_by_id = {p.id: p for p in participants}
    for team_result in result.teams:
        team = teams[team_result.index]
        team.strength_score = team_result.strength
        for pid in team_result.player_ids:
            assigned_by = AssignedBy.ADMIN if participant_by_id[pid].is_locked else AssignedBy.SYSTEM
            db.add(TeamMember(team_id=team.id, participant_id=pid, assigned_by=assigned_by))
            participant_by_id[pid].is_substitute = False
    for pid in result.reserve_ids:
        participant_by_id[pid].is_substitute = True

    session.status = SessionStatus.TEAM_GENERATED
    audit_service.record(
        db,
        session_id=session_id,
        action="GENERATE_TEAMS",
        payload={"imbalance": result.imbalance, "regenerate_locked": regenerate_locked},
    )
    db.commit()
    return get_board(db, session_id)


def _find_team_member(db: Session, session_id: str, participant_id: str) -> TeamMember | None:
    team_ids = [t.id for t in _teams_for_session(db, session_id)]
    if not team_ids:
        return None
    return db.scalar(
        select(TeamMember).where(
            TeamMember.participant_id == participant_id, TeamMember.team_id.in_(team_ids)
        )
    )


def move_player(db: Session, session_id: str, participant_id: str, target_team_id: str | None) -> TeamBoardOut:
    session = get_session(db, session_id)
    _ensure_editable(session.status)
    participant = db.get(SessionParticipant, participant_id)
    if participant is None or participant.session_id != session_id:
        raise NotFoundError(f"Participant {participant_id} not found")

    affected_teams: list[Team] = []
    current = _find_team_member(db, session_id, participant_id)
    if current is not None:
        source_team = db.get(Team, current.team_id)
        if source_team:
            affected_teams.append(source_team)
        db.delete(current)
        db.flush()

    if target_team_id is None:
        participant.is_substitute = True
    else:
        target_team = db.get(Team, target_team_id)
        if target_team is None or target_team.session_id != session_id:
            raise NotFoundError(f"Team {target_team_id} not found")
        db.add(TeamMember(team_id=target_team_id, participant_id=participant_id, assigned_by=AssignedBy.ADMIN))
        participant.is_substitute = False
        affected_teams.append(target_team)
    db.flush()

    for team in affected_teams:
        _recompute_strength(db, team)

    audit_service.record(
        db,
        session_id=session_id,
        action="MOVE_PLAYER",
        payload={"participant_id": participant_id, "target_team_id": target_team_id},
    )
    db.commit()
    return get_board(db, session_id)


def swap_players(db: Session, session_id: str, participant_id_a: str, participant_id_b: str) -> TeamBoardOut:
    session = get_session(db, session_id)
    _ensure_editable(session.status)
    if participant_id_a == participant_id_b:
        raise ValidationFailedError("Không thể swap một người với chính họ.")

    tm_a = _find_team_member(db, session_id, participant_id_a)
    tm_b = _find_team_member(db, session_id, participant_id_b)
    pa = db.get(SessionParticipant, participant_id_a)
    pb = db.get(SessionParticipant, participant_id_b)
    if pa is None or pa.session_id != session_id or pb is None or pb.session_id != session_id:
        raise NotFoundError("Participant not found in this session")

    team_a_id = tm_a.team_id if tm_a else None
    team_b_id = tm_b.team_id if tm_b else None

    if tm_a is not None:
        db.delete(tm_a)
    if tm_b is not None:
        db.delete(tm_b)
    db.flush()

    if team_b_id is not None:
        db.add(TeamMember(team_id=team_b_id, participant_id=participant_id_a, assigned_by=AssignedBy.ADMIN))
        pa.is_substitute = False
    else:
        pa.is_substitute = True

    if team_a_id is not None:
        db.add(TeamMember(team_id=team_a_id, participant_id=participant_id_b, assigned_by=AssignedBy.ADMIN))
        pb.is_substitute = False
    else:
        pb.is_substitute = True
    db.flush()

    for team_id in {team_a_id, team_b_id} - {None}:
        team = db.get(Team, team_id)
        if team:
            _recompute_strength(db, team)

    audit_service.record(
        db,
        session_id=session_id,
        action="SWAP",
        payload={"participant_a": participant_id_a, "participant_b": participant_id_b},
    )
    db.commit()
    return get_board(db, session_id)


def toggle_lock(db: Session, session_id: str, participant_id: str, is_locked: bool) -> TeamBoardOut:
    get_session(db, session_id)
    participant = db.get(SessionParticipant, participant_id)
    if participant is None or participant.session_id != session_id:
        raise NotFoundError(f"Participant {participant_id} not found")
    participant.is_locked = is_locked
    db.commit()
    return get_board(db, session_id)


def set_colors(db: Session, session_id: str, colors: dict[str, str]) -> TeamBoardOut:
    session = get_session(db, session_id)
    _ensure_editable(session.status)
    teams = {t.id: t for t in _teams_for_session(db, session_id)}
    for team_id in colors:
        if team_id not in teams:
            raise NotFoundError(f"Team {team_id} not found in session {session_id}")

    resulting = {t.id: (colors.get(t.id) or t.color) for t in teams.values()}
    if len(set(resulting.values())) != len(resulting):
        raise ValidationFailedError("Mỗi đội phải có một màu khác nhau trong cùng buổi đá (BR-07/BR-08).")

    for team_id, color in colors.items():
        teams[team_id].color = color

    audit_service.record(db, session_id=session_id, action="SET_COLORS", payload=colors)
    db.commit()
    return get_board(db, session_id)


def finalize(db: Session, session_id: str) -> MatchSession:
    """Validate BR-01..BR-08 before locking the session as FINALIZED (spec #45)."""
    session = get_session(db, session_id)
    if session.status == SessionStatus.PUBLISHED:
        raise ValidationFailedError("Buổi đá đã được Publish, không thể Finalize lại.")

    board = get_board(db, session_id)
    issues: list[str] = []

    if not board.teams:
        issues.append("Chưa có đội nào — vui lòng Generate trước khi Finalize.")

    if session.substitute_count is not None and len(board.reserve) != session.substitute_count:
        issues.append(
            f"Dự bị hiện có {len(board.reserve)} người, cấu hình yêu cầu {session.substitute_count} (BR-06)."
        )
    if session.player_per_team is not None:
        for t in board.teams:
            if len(t.members) != session.player_per_team:
                issues.append(f"{t.name} có {len(t.members)} người, cần đúng {session.player_per_team} (BR-06).")

    colors = [t.color for t in board.teams]
    if len(set(colors)) != len(colors):
        issues.append("Có đội trùng màu áo — mỗi đội cần một màu riêng (BR-07/BR-08).")

    if issues:
        raise ValidationFailedError(issues[0], issues)

    session.status = SessionStatus.FINALIZED
    audit_service.record(db, session_id=session_id, action="FINALIZE", payload={})
    db.commit()
    db.refresh(session)
    return session


def reopen(db: Session, session_id: str) -> MatchSession:
    """Explicit re-open required by BR-05 before editing a Finalized/Published session."""
    session = get_session(db, session_id)
    if session.status not in (SessionStatus.FINALIZED, SessionStatus.PUBLISHED):
        raise ValidationFailedError("Chỉ có thể Re-open khi buổi đá đã Finalize hoặc Published.")
    session.status = SessionStatus.TEAM_GENERATED
    audit_service.record(db, session_id=session_id, action="REOPEN", payload={})
    db.commit()
    db.refresh(session)
    return session
