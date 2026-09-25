"""Team Balancing Engine — deterministic, testable, no AI/LLM involved.

Implements "Version 1 — Greedy + Monte Carlo" from business-requirements.md
#24-31: sort players by skill score, greedily fill the currently weakest
team, repeat across many randomized iterations, keep the best (lowest
imbalance) solutions and randomly pick one of them — so the result still
*feels* random to the Admin (spec #30) while staying close to optimal.

`locked_team_index` lets Admin-locked players keep their team across a
Regenerate (spec #43-44): only unlocked players are reshuffled, but the
locked players' contribution to team strength/capacity is still respected.
"""

import math
import random
from dataclasses import dataclass

RESERVE = -1


class BalancingError(Exception):
    """Raised when the given configuration cannot produce a feasible assignment."""


@dataclass(frozen=True)
class PlayerInput:
    id: str
    skill_score: float
    locked_team_index: int | None = None  # None=unlocked, RESERVE=-1, else 0..team_count-1


@dataclass
class TeamResult:
    index: int
    player_ids: list[str]
    strength: float


@dataclass
class BalancingResult:
    teams: list[TeamResult]
    reserve_ids: list[str]
    imbalance: float


def balance_label(difference: float) -> str:
    if difference <= 1.0:
        return "Tốt"
    if difference <= 2.5:
        return "Khá"
    return "Chênh lệch lớn"


def generate_teams(
    players: list[PlayerInput],
    *,
    team_count: int,
    players_per_team: int,
    reserve_count: int,
    iterations: int = 500,
    tie_tolerance: float = 0.01,
    rng: random.Random | None = None,
) -> BalancingResult:
    rng = rng or random.Random()
    total = len(players)
    if team_count * players_per_team + reserve_count != total:
        raise BalancingError(
            f"{team_count} × {players_per_team} + {reserve_count} != {total} participants"
        )
    if team_count < 1:
        raise BalancingError("team_count must be >= 1")

    locked_reserve = [p for p in players if p.locked_team_index == RESERVE]
    locked_by_team: dict[int, list[PlayerInput]] = {i: [] for i in range(team_count)}
    for p in players:
        if p.locked_team_index is not None and p.locked_team_index != RESERVE:
            if not (0 <= p.locked_team_index < team_count):
                raise BalancingError(f"invalid locked_team_index {p.locked_team_index}")
            locked_by_team[p.locked_team_index].append(p)

    free = [p for p in players if p.locked_team_index is None]

    needed_reserve = reserve_count - len(locked_reserve)
    if needed_reserve < 0:
        raise BalancingError("More players locked to reserve than reserve_count allows")
    if needed_reserve > len(free):
        raise BalancingError("Not enough unlocked players left to fill the reserve")

    base_sum = {i: sum(p.skill_score for p in locked_by_team[i]) for i in range(team_count)}
    base_capacity = {i: players_per_team - len(locked_by_team[i]) for i in range(team_count)}
    for i, cap in base_capacity.items():
        if cap < 0:
            raise BalancingError(f"Team {i} has more locked players than its capacity")

    best_imbalance: float | None = None
    best_candidates: list[BalancingResult] = []

    for _ in range(max(1, iterations)):
        pool = free[:]
        rng.shuffle(pool)
        reserve_selected = pool[:needed_reserve]
        remaining = pool[needed_reserve:]
        remaining.sort(key=lambda p: -p.skill_score)

        sums = dict(base_sum)
        capacity = dict(base_capacity)
        assignment = {i: [p.id for p in locked_by_team[i]] for i in range(team_count)}

        feasible = True
        for p in remaining:
            eligible = [i for i in range(team_count) if capacity[i] > 0]
            if not eligible:
                feasible = False
                break
            min_sum = min(sums[i] for i in eligible)
            tied = [i for i in eligible if math.isclose(sums[i], min_sum, abs_tol=1e-9)]
            chosen = rng.choice(tied)
            assignment[chosen].append(p.id)
            sums[chosen] += p.skill_score
            capacity[chosen] -= 1
        if not feasible:
            continue

        imbalance = max(sums.values()) - min(sums.values())
        result = BalancingResult(
            teams=[
                TeamResult(index=i, player_ids=assignment[i], strength=sums[i])
                for i in range(team_count)
            ],
            reserve_ids=[p.id for p in locked_reserve] + [p.id for p in reserve_selected],
            imbalance=imbalance,
        )
        if best_imbalance is None or imbalance < best_imbalance - 1e-9:
            best_imbalance = imbalance
            best_candidates = [result]
        elif math.isclose(imbalance, best_imbalance, abs_tol=tie_tolerance):
            best_candidates.append(result)

    if best_imbalance is None:
        raise BalancingError("Could not generate a feasible team assignment")

    return rng.choice(best_candidates)
