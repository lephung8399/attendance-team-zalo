# Kế hoạch triển khai — Attendance & Team Balancer

Nguồn spec: [`docs/spec/business-requirements.md`](spec/business-requirements.md), [`docs/spec/technical-architecture.md`](spec/technical-architecture.md).

## Nguyên tắc dẫn đường

1. Zalo là adapter, không phải core. Toàn bộ luồng nghiệp vụ phải chạy được với `ManualAttendanceProvider` + `CopyMessagePublisher` trước, Zalo thật cắm vào sau mà không sửa core.
2. Chia đội = thuật toán deterministic (greedy + randomized restarts ở MVP), không AI.
3. Admin luôn có quyền override cuối cùng; hệ thống chỉ đề xuất.
4. Lưu snapshot & audit từ ngày đầu (skill snapshot theo session, ai generate/move/swap/finalize/publish) để làm nền AI-ready sau này.

## Kiến trúc

```
frontend/   Next.js 15 + TypeScript + Tailwind — Admin UI, phong cách tối giản kiểu Claude
backend/    FastAPI modular monolith (members / matches / attendance / teams / balancing / publishing / integrations.zalo)
db/         PostgreSQL 16+ qua SQLAlchemy 2 + Alembic (dev có thể chạy SQLite qua cùng models để không cần Docker)
```

Xem chi tiết cấu trúc thư mục trong technical-architecture.md.

## Phân kỳ (mỗi phase là một tập PR/commit độc lập, có thể demo được)

### Phase 0 — Nền tảng repo (hoàn thành trong đợt này)
- Lưu spec vào `docs/spec/`.
- Scaffold backend FastAPI + SQLAlchemy models cho toàn bộ core entities.
- Scaffold frontend Next.js + design system tối giản.
- Docker Compose cho dev (Postgres + backend + frontend).

### Phase 1 — Core MVP (trọng tâm đợt triển khai này)
Tính năng lớn, ảnh hưởng trực tiếp luồng sản phẩm — ưu tiên implement đầy đủ, có test:

1. **Member Management** — CRUD member, skill level/score, trạng thái active/inactive.
2. **Match Session** — tạo buổi đá, state machine `DRAFT→OPEN→LOCKED→TEAM_GENERATED→FINALIZED→PUBLISHED`.
3. **Attendance / Participant Review** — thêm member có sẵn, thêm Guest (auto-generate tên), xoá participant, override skill riêng cho session, snapshot skill tại thời điểm session.
4. **Team Configuration** — auto-suggest số đội/số người/dự bị theo participant count + rule configurable, validate tổng số khớp, cho phép Admin override.
5. **Balancing Engine** — thuật toán randomized-greedy tối thiểu hoá chênh lệch tổng skill giữa các đội, chạy nhiều iteration chọn lời giải tốt nhất, có yếu tố random giữa các lời giải tương đương.
6. **Team Board** — xem đội theo cột, move/swap participant giữa các đội & reserve, tính lại strength realtime, lock player trước khi regenerate, cảnh báo (không chặn) khi lệch nhiều.
7. **Team Colors** — auto-assign theo số đội, Admin đổi màu, không trùng màu trong 1 trận.
8. **Finalize** — validate đầy đủ điều kiện (BR-01…BR-08) trước khi khoá kết quả.
9. **Publish** — render `MessageTemplate` (placeholder), preview, `Copy Message` (luôn có), `Publish to Zalo` qua `MessagePublisher` adapter (MVP dùng `NullZaloPublisher`/`ManualPublisher` ghi log, sẵn interface cắm Zalo thật ở Phase 2), lưu `PublishLog`, hỗ trợ Retry khi fail.
10. **Audit trail tối thiểu** — ghi lại generate/move/swap/finalize/publish để phục vụ BR-05 và dữ liệu tương lai.

### Phase 2 — Zalo Integration thật + Automation

**Cập nhật (PoC đã chạy — không dùng Zalo OA/GMF như dự tính ban đầu):**

Đã xác nhận qua source code SDK chính thức (`python-zalo-bot`) rằng nền tảng thực tế dùng là **Zalo Bot Platform** (`bot.zaloplatforms.com`), một HTTP API kiểu Telegram Bot API (`POST {base}/bot{token}/{method}`), **không có endpoint đọc poll/vote nào cả** — xác nhận đúng nghi ngờ ở mục 68: Source A (đọc poll) không khả thi. Đã triển khai:

- `integrations/zalo/client.py` — `ZaloBotClient` gọi `getMe`/`sendMessage`/`getUpdates` thật.
- `integrations/zalo/publisher.py` — `ZaloMessagePublisher` thật, tự động được dùng khi có `ZALO_BOT_TOKEN` + `ZALO_GROUP_CHAT_ID`, nếu không có thì fallback `NullMessagePublisher` (Copy Message) — đúng nguyên tắc "Zalo không phải core".
- `integrations/zalo/attendance_provider.py` — `ZaloCheckinAttendanceProvider` (**Source B**): member gõ từ khoá (mặc định "tham gia") trong group, bot nhặt qua `getUpdates` polling (không cần webhook/domain public), tự tạo Member mới nếu chưa có (map theo `zalo_user_id`) — thoả FR-02. Idempotent qua bảng `zalo_poll_state` lưu `last_update_id`.
- Endpoint `POST /api/sessions/{id}/sync-attendance/zalo` — Admin bấm "Đồng bộ từ Zalo" trên UI.

**Còn lại cho Phase 2 đầy đủ:**
- Webhook (thay vì polling thủ công qua nút bấm) để tự động nhận check-in real-time — cần domain HTTPS public.
- Redis + worker (Dramatiq) cho publish/sync bất đồng bộ + retry, polling định kỳ nếu chưa dùng webhook.

### Phase 3 — Smart Engine
- OR-Tools solver thay thế/bổ sung greedy engine, thêm constraint vị trí/GK, reserve rotation công bằng theo lịch sử.

### Phase 4 — AI
- LLM parse constraint ngôn ngữ tự nhiên → structured constraints → đưa vào solver Phase 3.
- pgvector + ML player rating dựa trên lịch sử đã lưu từ Phase 1.

## Phạm vi KHÔNG làm ở đợt này (đúng theo spec mục 66)
AI/LLM chia đội, player statistics/ML, dự đoán skill tự động, cân bằng theo vị trí phức tạp, tối ưu công bằng theo lịch sử, mobile app, multi-club SaaS, payment.

## Định nghĩa "xong" cho Phase 1 (map theo mục 69–70 spec)

Admin thực hiện được trọn luồng qua UI, không cần Excel/tool ngoài:
Tạo session → thêm 24 participants (import/manual) → thêm 2 Guest → xoá 1 người → hệ thống tính lại 25 → cấu hình đội (3×8+1 hoặc override) → Generate → xem balance score → swap 2 người (strength cập nhật realtime) → chọn màu → Finalize (validate) → Preview message → Copy hoặc Publish.

Các test tự động (`backend/tests/`) cover trực tiếp Scenario A–E của spec (24 người 3×7+3 dự bị, 15 người 2×7+1 dự bị, Guest tham gia balancer, Admin override không bị tự undo, Publish lỗi vẫn giữ dữ liệu + Retry/Copy).

## UI/UX

Phong cách tối giản kiểu Claude: nền be/trắng ấm, một accent màu duy nhất (terracotta/rust), nhiều khoảng trắng, typography rõ ràng (Inter cho UI), bo góc mềm, đường viền mảnh thay vì đổ bóng nặng, chuyển động tinh tế. 6 màn hình chính theo mục 64 spec: Dashboard, Members, Session/Attendance, Team Configuration, Team Board (drag & drop), Publish.
