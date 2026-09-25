"""Placeholder for the Zalo OA webhook receiver (Phase 2).

Once the technical spike (business-requirements.md #68) confirms Zalo can
push registration/poll events, this module will expose a FastAPI router that
verifies the webhook signature and calls into
`app.modules.attendance.service.sync_attendance` with a `ZaloAttendanceProvider`
built from the payload — the attendance sync contract itself won't change.
"""
