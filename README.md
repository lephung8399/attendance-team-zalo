# Điểm danh & Chia đội bóng — tích hợp Zalo

Hệ thống thay thế quy trình thủ công (vote Zalo → tự nhớ trình độ → chia đội bằng tay → gõ lại vào Zalo) bằng một luồng có thể lặp lại mỗi tuần: điểm danh → cấu hình đội → chia đội cân bằng tự động → Admin điều chỉnh → công bố.

- **Spec gốc:** [`docs/spec/business-requirements.md`](docs/spec/business-requirements.md), [`docs/spec/technical-architecture.md`](docs/spec/technical-architecture.md)
- **Kế hoạch triển khai theo phase:** [`docs/PLAN.md`](docs/PLAN.md)

Trạng thái hiện tại: **Phase 1 (Core MVP) hoàn chỉnh + Phase 2 (Zalo thật) một phần** — chạy được toàn bộ luồng end-to-end mà không cần Zalo (xem nguyên tắc kiến trúc bên dưới), và đã cắm được Zalo Bot Platform thật cho publish + check-in.

## Kiến trúc

```
backend/    FastAPI modular monolith (Python) — members / matches / attendance /
            teams / balancing / publishing / integrations.zalo
frontend/   Next.js 16 + TypeScript + Tailwind — Admin UI tối giản kiểu Claude
docker-compose.yml   Postgres + backend + frontend cho môi trường gần-production
```

Ba nguyên tắc dẫn đường (chi tiết ở spec mục 72):

1. **Zalo không phải core system** — chỉ là adapter (`AttendanceProvider` / `MessagePublisher`). Toàn bộ app chạy tốt với `ManualAttendanceProvider` + `Copy Message`; Zalo thật cắm vào sau ở Phase 2 mà không sửa core.
2. **Không dùng AI để chia đội** — Team Balancing Engine là thuật toán randomized-greedy có thể test, reproduce, giải thích (xem `backend/app/modules/balancing/engine.py`).
3. **Admin luôn quyết định cuối cùng** — hệ thống chỉ đề xuất; Admin move/swap/lock/regenerate tự do, chỉ khi Finalize kết quả mới chính thức.

## Chạy nhanh bằng Docker

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (docs tại `/docs`)
- Frontend: http://localhost:3000

## Chạy dev thủ công (không cần Docker)

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head        # hoặc bỏ qua — SQLite dev tự tạo bảng khi khởi động
uvicorn app.main:app --reload
```

Mặc định dùng SQLite (`sqlite:///./attendance.db`) — không cần cài Postgres để phát triển. Set `APP_DATABASE_URL` để trỏ sang Postgres.

**Cắm Zalo thật (tuỳ chọn):** đăng ký bot tại [bot.zaloplatforms.com](https://bot.zaloplatforms.com), mời bot vào group, rồi set 2 biến môi trường (không có tiền tố `APP_`):

```bash
export ZALO_BOT_TOKEN="<token bot>"
export ZALO_GROUP_CHAT_ID="<chat_id của group, dạng zgr-...>"
```

Không set thì hệ thống tự dùng `NullMessagePublisher`/`ManualAttendanceProvider` — Copy Message và đồng bộ thủ công luôn hoạt động. Có thể đổi từ khoá check-in mặc định ("tham gia") qua `ZALO_CHECKIN_KEYWORD`.

Chạy test:

```bash
pytest
```

Bộ test (`backend/tests/`) cover thuật toán chia đội và toàn bộ 5 acceptance scenario A–E trong spec (24 người → 3×7+3, 15 người → 2×7+1, Guest tham gia balancer, Admin override không bị tự undo, Publish lỗi vẫn giữ dữ liệu + Copy/Retry).

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # trỏ NEXT_PUBLIC_API_URL sang backend
npm run dev
```

Mở http://localhost:3000.

## Luồng sử dụng (MVP)

1. **Thành viên** — tạo danh sách thành viên cố định + trình độ (Giỏi/TB/Yếu/Không rõ).
2. **Tạo buổi đá** — Dashboard → "+ Tạo buổi đá".
3. **Điểm danh** — bấm "Đồng bộ từ Zalo" (member gõ từ khoá "tham gia" trong group, cần đã cấu hình `ZALO_BOT_TOKEN`/`ZALO_GROUP_CHAT_ID`) hoặc chọn thủ công (luôn hoạt động, không phụ thuộc Zalo); thêm khách, xoá người nghỉ.
4. **Cấu hình đội** — hệ thống đề xuất số đội/số người/dự bị theo số người tham gia; Admin có thể override, có validate tức thời.
5. **Chia đội** — bấm Generate, xem balance score; kéo-thả hoặc dùng "Chế độ Swap" để điều chỉnh; khoá (lock) người trước khi chia lại.
6. **Công bố** — Finalize để khoá kết quả, xem preview tin nhắn, Copy Message (luôn có) hoặc Publish to Zalo (tự động dùng Zalo thật nếu đã cấu hình).

## Roadmap

Xem chi tiết ở [`docs/PLAN.md`](docs/PLAN.md). Tóm tắt:

- **Phase 1 (đã có):** Member/Session/Attendance/Team/Balancing/Publish core, chạy không cần Zalo.
- **Phase 2:** PoC Zalo thật (webhook, publish, poll), Redis + worker cho sync/publish bất đồng bộ.
- **Phase 3:** OR-Tools solver, ràng buộc vị trí/thủ môn, xoay vòng dự bị công bằng.
- **Phase 4:** LLM parse ràng buộc ngôn ngữ tự nhiên → constraints cho solver, ML player rating dựa trên lịch sử đã lưu từ Phase 1.
