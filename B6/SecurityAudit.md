# Security Audit — Social Network API (Auth & Posts)

Phạm vi: 3 endpoint trong `openapi.yaml` — `POST /auth/login`, `POST /auth/refresh`, `GET /posts/{id}`.
Mỗi mục nêu: **điểm có thể lộ**, **kịch bản tấn công**, **mức độ**, **biện pháp đã ghi trong spec**, **cách kiểm thử**.
Ánh xạ theo OWASP API Security Top 10 2023.

## Tóm tắt

| # | Điểm có thể lộ | Endpoint | OWASP | Mức độ |
|---|---|---|---|---|
| 1 | Dò tài khoản qua thông báo lỗi / thời gian phản hồi | `POST /auth/login` | API2 | High |
| 2 | Brute-force / credential stuffing | `POST /auth/login` | API2, API4 | High |
| 3 | Mật khẩu, token bị ghi vào log hoặc cache | login, refresh | API2, API8 | High |
| 4 | Refresh token bị đánh cắp và dùng lại | `POST /auth/refresh` | API2 | Critical |
| 5 | JWT bị giả mạo (`alg=none`, nhầm HS↔RS, không kiểm `aud`/`iss`) | refresh, posts | API2 | Critical |
| 6 | Quyền cũ còn trong token sau khi đổi role / khóa tài khoản | refresh, posts | API5 | Medium |
| 7 | BOLA — đọc bài `private`/`friends` của người khác | `GET /posts/{id}` | API1 | Critical |
| 8 | Liệt kê ID bài viết / lộ sự tồn tại của bài riêng tư | `GET /posts/{id}` | API1 | Medium |
| 9 | Lộ dữ liệu thừa trong response (email, IP, cờ nội bộ) | `GET /posts/{id}` | API3 | High |
| 10 | Blocklist/kho phiên lỗi → bỏ qua kiểm tra (fail-open) | refresh, posts | API2, API8 | High |
| 11 | Token lưu ở `localStorage` bị lấy qua XSS | client | API8 | High |
| 12 | Lộ chi tiết nội bộ qua lỗi 500 / cấu hình CORS lỏng | tất cả | API8 | Medium |

---

## 1. Dò tài khoản qua login (User enumeration)

- **Kịch bản:** Trả `"email không tồn tại"` khác với `"sai mật khẩu"`, hoặc email không tồn tại trả về nhanh hơn rõ rệt (bỏ qua bước hash). Kẻ tấn công lập được danh sách email có tài khoản để tấn công tiếp.
- **Biện pháp trong spec:** Một lỗi duy nhất `401 invalid_credentials` cho cả hai trường hợp; khi email không tồn tại vẫn chạy verify Argon2id với hash giả để cân bằng thời gian. `403 account_disabled` / `email_not_verified` chỉ trả **sau khi** mật khẩu đúng.
- **Kiểm thử:** Gửi email có/không tồn tại với mật khẩu sai → body và status phải giống nhau; đo thời gian phản hồi 100 lần mỗi loại, chênh lệch trung bình không đáng kể.

## 2. Brute-force và credential stuffing

- **Kịch bản:** Thử hàng nghìn mật khẩu cho một tài khoản, hoặc thử danh sách email:password rò rỉ từ dịch vụ khác trên nhiều tài khoản.
- **Biện pháp trong spec:** Rate-limit theo IP **và** theo tài khoản, trả `429` + `Retry-After`; không khóa cứng tài khoản (tránh kẻ xấu cố tình khóa người khác). `password.maxLength = 128` để tránh request gây tốn CPU khi hash.
- **Bổ sung khi triển khai:** Theo dõi tỉ lệ đăng nhập thất bại toàn hệ thống; cân nhắc MFA cho tài khoản quản trị.
- **Kiểm thử:** Gửi > N request sai liên tiếp → nhận `429`; gửi password 1 MB → bị chặn `400` trước khi hash.

## 3. Mật khẩu / token bị lộ qua log, cache, URL

- **Kịch bản:** Middleware log toàn bộ request body (chứa mật khẩu) hoặc header `Authorization`; proxy/CDN cache response chứa token; token đặt trong query string xuất hiện ở access log và lịch sử trình duyệt.
- **Biện pháp trong spec:** Token chỉ đi qua header `Authorization: Bearer`; response login/refresh có `Cache-Control: no-store`; ghi rõ "không log body login".
- **Bổ sung khi triển khai:** Bộ lọc log che (`***`) các trường `password`, `access_token`, `refresh_token`, header `Authorization`.
- **Kiểm thử:** Đăng nhập rồi `grep` log ứng dụng/gateway tìm mật khẩu mẫu và chuỗi `eyJ` → không được có kết quả.

## 4. Refresh token bị đánh cắp và dùng lại

- **Kịch bản:** Refresh token sống 30 ngày. Nếu bị lấy cắp, kẻ tấn công có thể tạo access token mới liên tục trong suốt thời gian đó, kể cả khi nạn nhân đã "đăng xuất" (code mẫu trên slide chưa có route logout và chưa thu hồi refresh token).
- **Biện pháp trong spec:** Refresh token **một lần dùng, xoay vòng** mỗi lần refresh; lưu `jti` trong kho phiên. Nếu refresh token đã dùng bị gửi lại → thu hồi cả family phiên, trả `401 token_reused` (cả kẻ tấn công lẫn người dùng thật phải đăng nhập lại — phát hiện được việc bị đánh cắp). Gửi access token vào `/auth/refresh` → `401 wrong_token_type`.
- **Kiểm thử:** Gọi `/auth/refresh` hai lần với cùng một refresh token → lần 2 nhận `401 token_reused`, và refresh token mới cấp ở lần 1 cũng bị vô hiệu.

## 5. JWT bị giả mạo hoặc dùng nhầm dịch vụ

- **Kịch bản:**
  - Token có header `alg: none` được chấp nhận nếu thư viện tin `alg` trong token.
  - Algorithm confusion: server dùng RS256 nhưng chấp nhận token HS256 ký bằng chính public key.
  - Token cấp cho dịch vụ khác (cùng khóa ký) được chấp nhận vì không kiểm `aud`/`iss`.
  - `JWT_SECRET_KEY` yếu hoặc bị commit lên Git → ai cũng ký được token hợp lệ.
- **Biện pháp trong spec:** Thuật toán lấy từ allowlist cấu hình phía server; bắt buộc kiểm `exp`, `iss`, `aud`, `type`; access token TTL 15 phút.
- **Bổ sung khi triển khai:** Khóa HS256 ngẫu nhiên ≥ 256 bit lấy từ secret manager/biến môi trường; header `kid` để xoay khóa; bật quét secret trong repo (pre-commit / CI).
- **Kiểm thử:** Sửa header thành `{"alg":"none"}` và bỏ chữ ký → `401`; ký token bằng khóa khác → `401`; đổi `aud` thành `other-api` → `401`.

## 6. Quyền cũ còn trong token (stale claims)

- **Kịch bản:** Scope/role được nhúng vào JWT lúc đăng nhập. Khi user bị hạ quyền hoặc bị đình chỉ, token cũ vẫn mang quyền cũ. Code mẫu trên slide còn đưa `claims` vào **refresh token**, nên nếu refresh copy claims từ refresh token thì quyền cũ sống thêm tới 30 ngày.
- **Biện pháp trong spec:** `/auth/refresh` nạp lại role/scope **hiện tại** từ DB và kiểm trạng thái tài khoản (`403 account_disabled` nếu bị đình chỉ). Access token chỉ sống 15 phút nên quyền cũ tồn tại tối đa 15 phút.
- **Bổ sung khi triển khai:** Khi khóa tài khoản, thu hồi ngay toàn bộ refresh token của user và đưa `jti` các access token đang hoạt động vào blocklist.
- **Kiểm thử:** Đăng nhập, đổi role trong DB, gọi refresh → scope trong access token mới phải theo role mới.

## 7. BOLA — đọc bài viết của người khác

- **Kịch bản:** User A có token hợp lệ với `posts:read`, gọi `GET /posts/{id}` với id bài `private` của user B. Nếu server chỉ kiểm token + scope mà không kiểm quyền trên đối tượng, A đọc được bài của B (OWASP API1:2023).
- **Biện pháp trong spec:** Ngoài scope, kiểm quyền xem bài: `public`, hoặc là tác giả, hoặc `friends` và là bạn, hoặc có `posts:moderate`; đồng thời người gọi không bị tác giả chặn và bài chưa bị xóa.
- **Kiểm thử:** Ma trận test (tác giả / bạn / người lạ / người bị chặn / moderator) × (`public` / `friends` / `private` / đã xóa); mỗi ô có status kỳ vọng. Đặc biệt: người lạ đọc bài `friends` → `404`.

## 8. Liệt kê ID và lộ sự tồn tại của bài riêng tư

- **Kịch bản:** ID tuần tự (`/posts/1001`, `/posts/1002`…) cho phép quét toàn bộ bài viết và ước lượng số lượng bài. Nếu bài riêng tư trả `403` còn bài không tồn tại trả `404`, kẻ tấn công biết được bài nào tồn tại.
- **Biện pháp trong spec:** ID dạng ULID (không tuần tự), có `pattern` để trả `400` sớm khi sai định dạng; không đủ quyền xem → trả `404` giống hệt bài không tồn tại. `403` chỉ dùng cho thiếu scope.
- **Kiểm thử:** So sánh body/status giữa id ngẫu nhiên không tồn tại và id bài `private` của người khác → phải giống nhau.

## 9. Lộ dữ liệu thừa trong response (Excessive data exposure)

- **Kịch bản:** Handler trả nguyên bản ghi DB (`SELECT *`) nên response chứa `author.email`, `author.phone`, `ip_address`, `is_shadow_banned`, `deleted_at`…; client chỉ "ẩn" ở giao diện nhưng dữ liệu vẫn nằm trong JSON (OWASP API3:2023).
- **Biện pháp trong spec:** Schema `Post` và `AuthorSummary` dùng `additionalProperties: false` và chỉ liệt kê trường công khai; serialize qua DTO. Payload JWT dùng `sub` là ID, không chứa email/PII.
- **Kiểm thử:** Validate response thật với schema trong spec (contract test) — bất kỳ trường lạ nào làm test thất bại.

## 10. Kho phiên / blocklist lỗi → fail-open

- **Kịch bản:** Hàm `token_in_blocklist_loader` trên slide gọi Redis. Nếu Redis sập và code bắt exception rồi trả `False` ("chưa bị thu hồi"), token đã logout/thu hồi lại dùng được.
- **Biện pháp trong spec:** `/auth/refresh` trả `503 session_store_unavailable` khi kho phiên không truy cập được — từ chối thay vì bỏ qua kiểm tra (fail-closed).
- **Kiểm thử:** Tắt Redis trong môi trường test, gọi refresh và endpoint bảo vệ với token đã thu hồi → không được trả `200`.

## 11. Token lưu ở client bị lấy qua XSS

- **Kịch bản:** SPA lưu access/refresh token trong `localStorage`; một lỗi XSS (ví dụ nội dung bài viết render không escape) cho phép script đọc và gửi token ra ngoài.
- **Biện pháp đề xuất:** Escape/sanitize `content` bài viết khi render; đặt Content-Security-Policy. Với web client, cân nhắc mô hình BFF: refresh token nằm trong cookie `HttpOnly; Secure; SameSite=Strict` do backend quản lý, kèm chống CSRF.
- **Kiểm thử:** Tạo bài có nội dung `<script>…</script>` / `<img onerror=…>` → không được thực thi khi hiển thị.

## 12. Lộ thông tin qua lỗi 500 và CORS

- **Kịch bản:** Lỗi 500 trả stack trace, câu SQL, phiên bản framework. CORS cấu hình `Access-Control-Allow-Origin: *` kèm credentials, hoặc phản chiếu mọi `Origin`, cho phép trang độc hại gọi API thay người dùng.
- **Biện pháp trong spec:** `500` chỉ trả Problem Details chung kèm `trace_id`; chỉ phục vụ HTTPS.
- **Bổ sung khi triển khai:** Allowlist origin cụ thể; tắt debug mode (`FLASK_DEBUG=0`) ở production.
- **Kiểm thử:** Gây lỗi có chủ đích → response không chứa traceback; gửi request với `Origin: https://evil.example` → không có header CORS cho phép.

---

## Checklist trước khi ship

- [ ] Mọi endpoint mặc định yêu cầu xác thực; chỉ `/auth/login` là công khai (`security: []`).
- [ ] Verify JWT với allowlist thuật toán + kiểm `exp`, `iss`, `aud`, `type`.
- [ ] Refresh token xoay vòng, phát hiện dùng lại, có route logout thu hồi family phiên.
- [ ] Kiểm quyền trên đối tượng ở `GET /posts/{id}`, trả `404` khi không được xem.
- [ ] Response đi qua DTO, khớp schema (contract test).
- [ ] Rate-limit login và refresh; không log mật khẩu/token.
- [ ] Kho phiên lỗi → fail-closed.
