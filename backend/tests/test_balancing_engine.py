"""Unit tests for the Team Balancing Engine — pure functions, no DB.

Covers the acceptance scenarios in docs/spec/business-requirements.md #70.
"""

import random

import pytest

from app.modules.balancing.engine import BalancingError, PlayerInput, RESERVE, generate_teams


def make_players(gioi=0, trung_binh=0, yeu=0) -> list[PlayerInput]:
    players = []
    idx = 0
    for _ in range(gioi):
        players.append(PlayerInput(id=f"p{idx}", skill_score=3.0))
        idx += 1
    for _ in range(trung_binh):
        players.append(PlayerInput(id=f"p{idx}", skill_score=2.0))
        idx += 1
    for _ in range(yeu):
        players.append(PlayerInput(id=f"p{idx}", skill_score=1.0))
        idx += 1
    return players


def test_scenario_a_24_players_3x7_plus_3_reserve():
    players = make_players(gioi=6, trung_binh=12, yeu=6)  # 24 total
    result = generate_teams(
        players, team_count=3, players_per_team=7, reserve_count=3, iterations=200, rng=random.Random(1)
    )
    assert len(result.reserve_ids) == 3
    assert sum(len(t.player_ids) for t in result.teams) == 21
    for t in result.teams:
        assert len(t.player_ids) == 7
    # All players accounted for exactly once.
    all_ids = [pid for t in result.teams for pid in t.player_ids] + result.reserve_ids
    assert sorted(all_ids) == sorted(p.id for p in players)
    # Balance should be tight given a symmetric skill distribution.
    assert result.imbalance <= 2.0


def test_scenario_b_15_players_2x7_plus_1_reserve():
    players = make_players(gioi=4, trung_binh=7, yeu=4)  # 15 total
    result = generate_teams(
        players, team_count=2, players_per_team=7, reserve_count=1, iterations=200, rng=random.Random(2)
    )
    assert len(result.reserve_ids) == 1
    assert all(len(t.player_ids) == 7 for t in result.teams)


def test_invalid_configuration_raises():
    players = make_players(gioi=5)
    with pytest.raises(BalancingError):
        generate_teams(players, team_count=3, players_per_team=7, reserve_count=3, iterations=10)


def test_locked_player_keeps_team_across_regenerate():
    players = make_players(gioi=3, trung_binh=3)
    locked = players[0]
    locked_players = [
        PlayerInput(id=locked.id, skill_score=locked.skill_score, locked_team_index=1)
    ] + players[1:]
    result = generate_teams(
        locked_players, team_count=2, players_per_team=3, reserve_count=0, iterations=100, rng=random.Random(3)
    )
    team_1 = next(t for t in result.teams if t.index == 1)
    assert locked.id in team_1.player_ids


def test_locked_reserve_player_stays_in_reserve():
    players = make_players(gioi=2, trung_binh=2)
    locked_reserve = players[0]
    updated = [
        PlayerInput(id=locked_reserve.id, skill_score=locked_reserve.skill_score, locked_team_index=RESERVE)
    ] + players[1:]
    result = generate_teams(
        updated, team_count=1, players_per_team=3, reserve_count=1, iterations=50, rng=random.Random(4)
    )
    assert result.reserve_ids == [locked_reserve.id]


def test_random_factor_can_produce_different_solutions():
    """With many equally-balanced ties, repeated runs shouldn't always be identical (spec #30)."""
    players = make_players(trung_binh=8)  # all equal skill -> many tied optimal solutions
    seen = set()
    for seed in range(10):
        result = generate_teams(
            players, team_count=2, players_per_team=4, reserve_count=0, iterations=50, rng=random.Random(seed)
        )
        seen.add(tuple(sorted(result.teams[0].player_ids)))
    assert len(seen) > 1
