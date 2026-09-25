# Business Requirement Document — Hệ thống Điểm danh & Chia đội bóng tích hợp Zalo

**Phiên bản:** 1.0
**Trạng thái:** Draft (nguồn gốc)
**Ghi chú:** Tài liệu này được import nguyên trạng từ bản đề xuất Business Analysis / SRS ban đầu, dùng làm nguồn tham chiếu cho toàn bộ quá trình triển khai. Kế hoạch thực thi chi tiết nằm ở [`docs/PLAN.md`](../PLAN.md).

---

Dưới đây là phiên bản tôi đề xuất theo hướng **Business Analysis / Software Requirement Specification**. Tôi chủ động tách module **Zalo Integration** khỏi core business vì đây là phần cần làm PoC sớm nhất: tài liệu Zalo hiện có nhóm tính năng quản lý nhóm **GMF** và OA có khả năng gửi tin vào nhóm, nhưng từ tài liệu công khai tôi chưa xác nhận được API chính thức nào cho phép đọc trực tiếp kết quả của một poll/vote đã tạo trong group Zalo.

# 1. Tổng quan dự án

## 1.1. Bối cảnh

Hiện tại việc tổ chức các buổi đá bóng được thực hiện chủ yếu thông qua Zalo Group.

Quy trình hiện tại:

1. Admin tạo bình chọn/vote trong nhóm Zalo để xác nhận người tham gia.
2. Thành viên vote tham gia.
3. Admin kiểm tra danh sách người đã vote.
4. Admin nhập hoặc copy danh sách ra bên ngoài.
5. Admin tự đánh giá hoặc nhớ trình độ từng người.
6. Admin chia người thành các đội bằng phương pháp thủ công hoặc random.
7. Admin điều chỉnh lại đội nếu nhận thấy chênh lệch trình độ.
8. Admin chọn màu áo.
9. Admin nhập lại danh sách đội và gửi vào Zalo.

Vấn đề: nhiều thao tác thủ công, dễ nhập thiếu/sai tên, mất thời gian khi số người thay đổi, random không đảm bảo cân bằng trình độ, khó thêm người ngoài group, phải lặp lại toàn bộ quy trình mỗi tuần, thông tin trình độ không tập trung, format lại kết quả trên Zalo mất thời gian.

# 2. Business Goal

Rút gọn quy trình:

**Vote Zalo → Danh sách tham gia → Điều chỉnh danh sách → Chia đội cân bằng → Admin chỉnh sửa → Công bố lên Zalo**

Mục tiêu chính: giảm tối đa thao tác nhập liệu thủ công; lưu trữ thông tin thành viên lâu dài; hỗ trợ số lượng người tham gia biến động; chia đội tự động nhưng cân bằng; cho phép Admin can thiệp trước/sau khi chia; hỗ trợ khách; quản lý màu áo; gửi kết quả về Zalo.

# 3. Phạm vi hệ thống

7 module chính: Zalo Integration, Member Management, Match Session Management, Attendance Management, Team Configuration, Team Balancing Engine, Publishing / Zalo Bot.

# 4. Actor

## 4.1 Admin
Người tổ chức buổi đá. Quyền: quản lý thành viên, đánh giá trình độ, tạo buổi đá, đồng bộ danh sách vote, thêm/xóa người tham gia, thêm khách, thiết lập số đội/số người mỗi đội, chia đội, chỉnh sửa đội, chọn màu, công bố kết quả.

## 4.2 Member
Thành viên cố định trong group, thông tin lưu lâu dài. Có thể vote tham gia trên Zalo, xuất hiện trong attendance của buổi đá. MVP chưa cần giao diện riêng cho Member.

## 4.3 Guest
Người tham gia một buổi nhưng không có trong group Zalo, chưa có tài khoản, hoặc Admin chưa biết tên (Guest 01, Guest 02, Khách của Nam...). Guest chỉ tồn tại trong một Match Session trừ khi được chuyển thành Member.

# 5. Business Flow tổng thể

```
ZALO GROUP → Member vote → POLL/ATTENDANCE → SYNC DATA → MATCH SESSION
  (Member từ Zalo / Add Member thủ công / Remove Member / Add Guest)
  → REVIEW PARTICIPANTS → TEAM CONFIGURATION (số đội, player/team, substitute, colors)
  → BALANCING ENGINE → DRAFT TEAMS → ADMIN REVIEW/EDIT → FINALIZE → PUBLISH TO ZALO
```

# 6–8. Module 1 — Zalo Integration

Thiết kế dạng Adapter, business logic KHÔNG phụ thuộc trực tiếp vào Zalo:

```
AttendanceProvider
    getParticipants()
    syncParticipants()

MessagePublisher
    sendMessage()
```

Implementation: `ZaloAttendanceProvider`, `ManualAttendanceProvider`, `FutureProvider`. Nếu Zalo API không cho phép lấy poll/vote trực tiếp, core vẫn hoạt động.

Nguồn lấy attendance:
- **Source A — Zalo Poll**: Zalo Poll → Zalo API/Webhook → Backend → Attendance (ưu tiên nếu API hỗ trợ).
- **Source B — Bot check-in**: Bot gửi tin nhắn có nút "THAM GIA", user tương tác, Backend ghi nhận.
- **Source C — Admin Import**: fallback MVP — paste danh sách, chọn member, import CSV, thêm tay.

# 9–11. Module 2 — Member Management

### Member Entity
| Field | Type | Description |
|---|---|---|
| id | UUID | Internal member ID |
| zalo_user_id | String nullable | Zalo UID nếu lấy được |
| display_name | String | Tên hiển thị |
| nickname | String | Tên thường dùng |
| skill_level | Enum | GIOI / TRUNG_BINH / YEU / UNKNOWN |
| skill_score | Decimal | Điểm trình độ |
| preferred_position | Enum nullable | Vị trí |
| status | Enum | Active / Inactive |
| note | Text | Ghi chú |
| created_at / updated_at | Timestamp | |

Skill Level lưu cả `skill_level` (enum hiển thị) và `skill_score` (decimal) để thuật toán dễ mở rộng (vd Minh = 2.8). Mặc định: Giỏi=3, Trung Bình=2, Yếu=1, Unknown=2 (configurable). Guest/member mới chưa rõ trình độ dùng `UNKNOWN`, Admin có thể override.

# 12–13. Module 3 — Match Session

`MatchSession`: id, title, play_date, start_time, location, zalo_group_id, poll_id, status, team_count, player_per_team, substitute_count, created_by, created_at.

Status flow: `DRAFT → OPEN → LOCKED → TEAM_GENERATED → FINALIZED → PUBLISHED`.

# 14–18. Module 4 — Attendance Management

Attendance không gắn trực tiếp vào Member (vì có Guest) → entity `SessionParticipant`:

| Field | Description |
|---|---|
| id | ID |
| session_id | Match session |
| member_id | Nullable |
| participant_name | Tên snapshot |
| participant_type | MEMBER / GUEST |
| skill_level / skill_score | Snapshot tại thời điểm session |
| attendance_source | ZALO / MANUAL / GUEST |
| attendance_status | CONFIRMED / WAITING / CANCELLED |
| is_substitute | Có phải dự bị |
| note | Ghi chú |

Skill cần snapshot vì lịch sử trận cũ không nên bị tính lại theo skill hiện tại của Member.

Thêm Guest: form Tên (auto-generate "Guest 01/02/.." nếu bỏ trống), Trình độ (mặc định Unknown), Người giới thiệu (optional), Ghi chú.

Participant Review Screen: sau khi sync, Admin phải review trước khi chia đội — add/remove, đổi skill tạm thời, rename Guest, đánh dấu nghỉ/dự bị thủ công, trước khi "Chốt danh sách".

# 19–23. Module 5 — Team Configuration

Auto Suggest dựa trên N = participant count, theo configuration (không hard-code):

```json
{
  "preferred_team_size": 7,
  "min_team_size": 6,
  "max_team_size": 8,
  "preferred_team_count": [2, 3]
}
```

Validation bắt buộc: `team_count × players_per_team + substitute_count = total participants`, không thỏa thì cảnh báo và không cho Finalize.

# 24–36. Module 6 — Team Balancing Engine

Mục tiêu: **Random trong phạm vi các đội có sức mạnh gần tương đương nhau**, KHÔNG dùng AI/LLM để chia đội.

`TeamStrength = Σ player.skill_score`. Objective: minimize `max(team_score) - min(team_score)` (hoặc variance).

- **V1 — Greedy + Monte Carlo**: sort giảm dần theo score, random giữa các player bằng điểm, đưa lần lượt vào team yếu nhất, random nhiều iteration (vd 10.000), chọn imbalance thấp nhất.
- **V2 — Optimization (Phase 3)**: OR-Tools / constraint programming, objective minimize variance, constraints: 1 player/1 team, đúng sĩ số, locked player giữ nguyên, sau này thêm GK/position/pair-history.

Random factor: với nhiều solution tương đương, random chọn 1 (không luôn ra cùng 1 kết quả). UI hiển thị Balance Score (vd "Team A: 14, Team B: 14, Team C: 13 — Balance: Tốt, Difference: 1") không bắt buộc show công thức.

Advanced attributes (Phase 2+, chưa MVP): attack/defense/goalkeeper/stamina score, position (GK/DEF/MID/ATT/FLEX), GK constraint (>=1/team), reserve rotation.

Substitute = một "bucket" riêng (Reserve), không phải Team; chọn thủ công hoặc để hệ thống chọn.

# 37–41. Module 7 — Team Colors & Entities

Default: WHITE, RED, BLUE. Auto-assign theo thứ tự nếu đủ 3 team; 2 team thì Admin chọn 2/3 màu, hệ thống nhớ config lần trước.

`Team`: id, session_id, name, color, strength_score (computed), order.
`TeamMember`: team_id, participant_id, assigned_by (SYSTEM/ADMIN), assigned_at.

Admin adjustment: drag & drop giữa các team, Swap 2 người (cập nhật Team Strength realtime, cảnh báo nếu lệch nhiều nhưng không cấm). Lock Player (🔒) giữ nguyên khi Regenerate — hỗ trợ "Generate All" hoặc "Generate Unlocked Players".

# 45–49. Finalize & Publish

Finalize validate: mọi participant đã phân bổ, không duplicate, team size đúng, màu không trùng (default rule), reserve đúng số lượng → `session.status = FINALIZED`.

Publish: Backend tạo message từ `MessageTemplate` (không hard-code nội dung, dùng placeholder `{{session_title}}`, `{{teams}}`, `{{reserves}}`, `{{location}}`, `{{start_time}}`, `{{footer}}`), Admin preview trước khi gửi.

Publish Flow: `FINALIZED → Generate Message → Preview → Admin Confirm → Zalo API → Success/Failed`.

Nếu Zalo API lỗi: không được mất kết quả, Admin có `[Retry]` và `[Copy Message]` (fallback bắt buộc).

# 50. Functional Requirements (FR-01 → FR-20)

FR-01 Member CRUD & skill. FR-02 Zalo↔Member mapping. FR-03 Session creation. FR-04 Attendance sync qua Attendance Provider. FR-05 Manual add existing member. FR-06 Add Guest (named/unnamed). FR-07 Remove participant trước Finalize. FR-08 Skill override riêng cho session (không đổi Member master). FR-09 Team config recommendation theo participant count. FR-10 Manual override team_count/team_size/reserve_count. FR-11 Auto balance theo skill score. FR-12 Randomization — nhiều balanced solutions. FR-13 Manual move/swap player giữa teams. FR-14 Assign team color. FR-15 Regenerate teams. FR-16 Lock player trước khi regenerate. FR-17 Validate trước Finalize. FR-18 Generate Zalo message. FR-19 Preview message trước publish. FR-20 Retry khi publish fail.

# 51. Business Rules (BR-01 → BR-10)

BR-01 Một participant chỉ thuộc 1 Team hoặc Reserve. BR-02 Không duplicate participant trong cùng session. BR-03 Guest không bắt buộc có Member ID. BR-04 Member master skill và session skill độc lập. BR-05 Sau Finalize, sửa phải Re-open Session hoặc có audit log. BR-06 Σ Team Players + Reserve = tổng participants. BR-07 Mỗi team chỉ 1 màu. BR-08 Trong cùng trận, màu team mặc định không trùng nhau. BR-09 Unknown skill phải có fallback score. BR-10 Manual Admin adjustment luôn ưu tiên hơn Auto Engine.

# 52–54. Data & API Design

Core entities: `User, Member, ZaloIdentity, Group, MatchSession, SessionParticipant, Team, TeamMember, MessageTemplate, PublishLog, MemberSkillHistory, AuditLog`.

ERD: `Member 1—N SessionParticipant N—1 MatchSession 1—N Team 1—N TeamMember` (Guest: `SessionParticipant.member_id = NULL`).

API design tham khảo phần đầy đủ trong tài liệu gốc — tương ứng với các endpoint đã hiện thực tại `backend/app/api/*` (members, sessions, attendance, guests, team configuration, generate-teams, move-player, swap, finalize, publish-preview, publish).

# 55–59. Kiến trúc & nguyên tắc tách biệt

Core Domain (Member, Session, Participant, Team, Balancer) tách biệt hoàn toàn khỏi External Integration (Zalo) để có thể test toàn bộ hệ thống mà không cần Zalo. Audit Log ghi lại các hành động quan trọng (generate, move, swap, finalize, publish) — đặc biệt hữu ích khi nhiều Admin cùng thao tác.

# 60–62. History & Phase 2 features (không thuộc MVP)

Lưu lịch sử trận, fairness history (tránh cùng cặp/cùng dự bị liên tục), player statistics (matches_played, attendance_rate, reserve_count).

# 63. Non-functional Requirements

Performance: generate team < 1s cho 10–50 participants. Reliability: không mất draft nếu publish fail. Security: Zalo token lưu server-side, không gửi frontend, không log raw token. Auditability: Generate/Move/Swap/Finalize/Publish có log. Idempotency: sync Zalo nhiều lần không tạo duplicate participant (key: `session_id + zalo_user_id`).

# 64. UX Screen List (MVP ~6 màn hình)

1. Dashboard (Upcoming Match, participants count, [Manage]).
2. Members (danh sách + skill).
3. Session/Attendance (Sync Zalo, member list, Add Member/Guest).
4. Team Configuration (players/teams/players-per-team/reserve, Generate).
5. Team Board (drag/drop giữa các team + Reserve).
6. Publish (Preview, Copy, Publish to Zalo).

# 65–67. MVP Scope

**Trong MVP**: Member management, skill classification, match session, manual/import attendance, guest, dynamic team configuration, balanced random algorithm, team editing, team colors, message generation, copy message, Zalo publishing nếu API hỗ trợ.

**Không trong MVP**: AI/LLM, player statistics, machine learning, automatic skill prediction, complex position balancing, historical fairness optimization, mobile native app, multi-club SaaS, payment.

**Phase 2**: Zalo automation nâng cao, GK/Position balancing, reserve rotation, historical fairness, attendance statistics, member self-service, Mini App, multiple groups, multiple admins.

# 68. Technical Spike bắt buộc trước khi code Zalo

PoC riêng cho Zalo cần trả lời: OA/bot tham gia đúng loại group hiện tại? đọc được member/group info? lấy được dữ liệu poll/vote? nhận webhook khi đăng ký? gửi message chủ động vào group? format/message type hỗ trợ? permission/token lifecycle? rate limit/quota/cost? — Nếu câu (3) không khả thi: **KHÔNG block project**, chuyển sang Attendance Provider riêng / manual import.

# 69–70. Definition of MVP Success & Acceptance Scenarios

MVP thành công khi Admin thực hiện được toàn bộ luồng: Tạo buổi đá → 24 người → thêm 2 Guest → xóa 1 người nghỉ → hệ thống tính lại 25 người → cấu hình đội → Generate → cân bằng → swap 2 người → chọn màu → Finalize → tạo message → Publish/Copy — không cần Excel hay công cụ random ngoài.

Acceptance scenarios A–E (24 người → 3×7+3 reserve; 15 người → 2×7+1 reserve; Guest tham gia balancer bình thường; Admin move/swap cập nhật strength realtime không tự undo; Zalo lỗi → giữ session data, Retry hoặc Copy Message) — đã map trực tiếp vào bộ test backend (`backend/tests/`).

# 71–72. Kiến trúc nghiệp vụ & Product Principle

```
Zalo Group → Zalo Adapter → (Member DB +) Session Participants
  → Admin Review/Guest → Team Config → Balancing Engine → Draft Teams
  → Admin Adjust → Finalized Teams → Message Generator → Zalo Publisher → Zalo Group
```

**Ba nguyên tắc quan trọng nhất:**

1. **Zalo không phải core system** — chỉ là nguồn input và kênh output; nếu Zalo API đổi/không hỗ trợ Poll API thì hệ thống chia đội vẫn hoạt động.
2. **AI không nên quyết định việc chia đội** — dùng Team Balancing Engine có constraint/objective rõ ràng, kết quả test được, reproduce được, giải thích được.
3. **Admin luôn có quyền quyết định cuối cùng** — hệ thống chỉ đề xuất; Admin move/swap/lock/regenerate; chỉ khi Finalize thì kết quả mới chính thức.
