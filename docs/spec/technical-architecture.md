# Technical Architecture Recommendation — Attendance & Team Balancer

**Nguồn:** Import từ bản tư vấn kỹ thuật ban đầu (technical advisor), dùng làm cơ sở cho quyết định stack. Kế hoạch thực thi cụ thể ở [`docs/PLAN.md`](../PLAN.md).

---

Kiến trúc đề xuất: **Python-first modular monolith** (chưa cần microservice), thiết kế sẵn để mở rộng AI ở các phase sau nhưng KHÔNG dùng AI để chia đội.

## Stack

| Layer | Công nghệ | Lý do |
|---|---|---|
| Frontend | Next.js + TypeScript | UI admin, drag/drop chia đội, responsive |
| Backend API | Python + FastAPI | Thuận lợi khi thêm AI/ML sau này |
| ORM | SQLAlchemy 2.x | Linh hoạt, mature, hợp PostgreSQL |
| Validation | Pydantic | Đi cùng FastAPI tự nhiên |
| Database | PostgreSQL 18 | Relational data rất phù hợp |
| Migration | Alembic | Quản lý schema/version DB |
| Cache/Job (Phase 2+) | Redis | Cache, queue, distributed lock |
| Async Job (Phase 2+) | Dramatiq/Celery | Zalo sync, publish retry, AI sau này |
| Team Engine | Python (greedy MVP → OR-Tools Phase 3) | Constraint optimization chia đội |
| AI layer (Phase 4) | Python module riêng | LLM, embeddings, ML |
| Vector DB (Phase 4) | pgvector trên PostgreSQL | Không cần thêm vector DB riêng |
| Deployment | Docker / Docker Compose | Dev/prod nhất quán |

## Nguyên tắc kiến trúc

1. **Modular monolith**, không tách microservices sớm. Một application, một database, boundary rõ theo module.
2. **Core Domain tách biệt Integration**: `members / matches / attendance / teams / balancing / publishing` là core; `integrations/zalo` chỉ là adapter (implements `AttendanceProvider`, `MessagePublisher`). Core phải chạy và test được mà không cần Zalo.
3. **AI Engine ≠ Team Balancing Engine**: balancing dùng thuật toán deterministic (constraint/optimization), không gửi dữ liệu chia đội sang LLM. LLM (Phase 4) chỉ dùng để parse ngôn ngữ tự nhiên → structured constraints → đưa vào solver.
4. **AI-ready data model ngay từ MVP**: lưu lịch sử `team_generation` (algorithm, parameters), `team_adjustment` (SWAP/MOVE, performed_by), `match_result` — đây là dữ liệu huấn luyện tương lai, quan trọng hơn việc chọn framework AI ngay bây giờ.

## Cấu trúc thư mục backend

```
backend/
├── app/
│   ├── api/                # FastAPI routers (HTTP layer mỏng)
│   ├── modules/
│   │   ├── members/        # models, schemas, repository, service
│   │   ├── matches/
│   │   ├── attendance/
│   │   ├── teams/
│   │   ├── balancing/      # engine.py, constraints.py, scorer.py
│   │   ├── publishing/
│   │   ├── ai/             # rỗng ở MVP, sẵn interface cho Phase 4
│   │   └── integrations/
│   │       └── zalo/       # client.py, webhook.py, publisher.py (adapter)
│   ├── database/
│   ├── workers/            # Phase 2+
│   └── main.py
├── migrations/              # Alembic
├── tests/
├── Dockerfile
└── pyproject.toml
```

## Roadmap công nghệ theo phase

- **Phase 1 — Core**: FastAPI + PostgreSQL + Next.js. Member, Match, Attendance, Team, Balancer (greedy), Manual/Copy publish. Không AI, không Redis bắt buộc.
- **Phase 2 — Automation**: Redis, worker, Zalo integration thật (webhook, publish retry, background sync).
- **Phase 3 — Smart Engine**: OR-Tools, position/GK constraints, reserve fairness, pair-history.
- **Phase 4 — AI**: LLM parse constraint tự nhiên, embeddings, ML player rating, historical learning.

## Quyết định chốt

> **Next.js + FastAPI + PostgreSQL**, kiến trúc **Modular Monolith + AI-ready data model**, balancing engine deterministic (không AI) ở MVP; OR-Tools và AI được thêm dần ở Phase 3/4 mà không cần viết lại hệ thống.
