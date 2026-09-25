"""API-level acceptance tests mirroring docs/spec/business-requirements.md #69-70:
the full Admin flow from creating a session to Publish/Copy, exercised through
the same HTTP endpoints the frontend calls.
"""


def create_member(client, name, skill_level="TRUNG_BINH"):
    resp = client.post("/api/members", json={"display_name": name, "skill_level": skill_level})
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_session(client, title="Thu 5"):
    resp = client.post(
        "/api/sessions",
        json={"title": title, "play_date": "2026-10-01", "start_time": "20:30:00", "location": "San ABC"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_full_mvp_flow(client):
    # 14 members from "Zalo" (manual sync stands in for it) + 1 guest = 15 (Scenario C)
    members = [create_member(client, f"Player {i}") for i in range(14)]
    session = create_session(client)
    sid = session["id"]

    sync_resp = client.post(
        "/api/sessions/{}/sync-attendance".format(sid), json={"member_ids": [m["id"] for m in members]}
    )
    assert sync_resp.status_code == 200
    assert len(sync_resp.json()) == 14

    guest_resp = client.post(f"/api/sessions/{sid}/guests", json={})
    assert guest_resp.status_code == 201
    assert guest_resp.json()["participant_name"] == "Guest 01"

    participants = client.get(f"/api/sessions/{sid}/participants").json()
    assert len(participants) == 15  # Scenario C: 14 members + 1 guest

    # Remove one member ("người nghỉ") -> 14 total participants left.
    removed_participant = participants[0]
    removed_member_id = removed_participant["member_id"]
    del_resp = client.delete(f"/api/sessions/{sid}/participants/{removed_participant['id']}")
    assert del_resp.status_code == 204
    participants = client.get(f"/api/sessions/{sid}/participants").json()
    assert len(participants) == 14

    # Add the same member back to reach 15 confirmed participants again, for a
    # clean 2x7+1 configuration (Scenario B).
    readd = client.post(f"/api/sessions/{sid}/participants", json={"member_id": removed_member_id})
    assert readd.status_code == 201, readd.text
    participants = client.get(f"/api/sessions/{sid}/participants").json()
    assert len(participants) == 15

    suggestions = client.get(f"/api/sessions/{sid}/team-suggestions").json()
    assert any(s["team_count"] == 2 and s["player_per_team"] == 7 and s["substitute_count"] == 1 for s in suggestions)

    config_resp = client.patch(
        f"/api/sessions/{sid}/configuration",
        json={"team_count": 2, "player_per_team": 7, "substitute_count": 1},
    )
    assert config_resp.status_code == 200
    assert config_resp.json()["status"] == "LOCKED"

    board = client.post(f"/api/sessions/{sid}/generate-teams", json={}).json()
    assert len(board["teams"]) == 2
    assert all(len(t["members"]) == 7 for t in board["teams"])
    assert len(board["reserve"]) == 1

    # Scenario D: Admin swap must stick and recompute strength — no auto-undo.
    a = board["teams"][0]["members"][0]["id"]
    b = board["teams"][1]["members"][0]["id"]
    swapped = client.post(f"/api/sessions/{sid}/teams/swap", json={"participant_id_a": a, "participant_id_b": b}).json()
    team_a_ids = {m["id"] for m in swapped["teams"][0]["members"]}
    team_b_ids = {m["id"] for m in swapped["teams"][1]["members"]}
    assert b in team_a_ids and a in team_b_ids

    # Regenerating again must not silently revert the manual swap unless Admin asks for it —
    # here we just confirm colors can be customized and are enforced unique (BR-07/08).
    team_ids = [t["id"] for t in swapped["teams"]]
    dup_colors = client.patch(f"/api/sessions/{sid}/teams/colors", json={"colors": {team_ids[0]: "RED", team_ids[1]: "RED"}})
    assert dup_colors.status_code == 400

    ok_colors = client.patch(f"/api/sessions/{sid}/teams/colors", json={"colors": {team_ids[0]: "WHITE", team_ids[1]: "RED"}})
    assert ok_colors.status_code == 200

    finalize_resp = client.post(f"/api/sessions/{sid}/finalize")
    assert finalize_resp.status_code == 200, finalize_resp.text
    assert finalize_resp.json()["status"] == "FINALIZED"

    # Post-finalize edits are blocked until Re-open (BR-05).
    blocked = client.post(f"/api/sessions/{sid}/guests", json={"name": "Late guest"})
    assert blocked.status_code == 400

    # Scenario E: publish fails (no Zalo connected yet) but session data + message survive.
    publish_resp = client.post(f"/api/sessions/{sid}/publish")
    assert publish_resp.status_code == 200
    body = publish_resp.json()
    assert body["success"] is False
    assert "Copy Message" in body["error"]
    assert "TEAM" in body["message"]

    session_after = client.get(f"/api/sessions/{sid}").json()
    assert session_after["status"] == "FINALIZED"  # not silently moved to PUBLISHED on failure

    # Retry is just calling publish again — still safe, still returns full data.
    retry_resp = client.post(f"/api/sessions/{sid}/publish")
    assert retry_resp.status_code == 200
    assert retry_resp.json()["attempt"] == 2

    logs = client.get(f"/api/sessions/{sid}/publish-logs").json()
    assert len(logs) == 2


def test_finalize_blocked_when_unassigned_participants(client):
    members = [create_member(client, f"P{i}") for i in range(6)]
    session = create_session(client, "Ad-hoc")
    sid = session["id"]
    client.post(f"/api/sessions/{sid}/sync-attendance", json={"member_ids": [m["id"] for m in members]})
    client.patch(f"/api/sessions/{sid}/configuration", json={"team_count": 2, "player_per_team": 3, "substitute_count": 0})

    # Finalize before Generate must fail with a clear reason.
    resp = client.post(f"/api/sessions/{sid}/finalize")
    assert resp.status_code == 400
    assert "Generate" in resp.json()["detail"]


def test_duplicate_member_rejected(client):
    member = create_member(client, "Solo")
    session = create_session(client, "Dup test")
    sid = session["id"]
    client.post(f"/api/sessions/{sid}/participants", json={"member_id": member["id"]})
    dup = client.post(f"/api/sessions/{sid}/participants", json={"member_id": member["id"]})
    assert dup.status_code == 400  # BR-02
