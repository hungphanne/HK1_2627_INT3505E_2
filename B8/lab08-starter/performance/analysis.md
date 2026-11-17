# Lab 4 — Phân tích kết quả

| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | | | |
| B | 50 | 5 | 60s | | | |
| C | 200 | 50 | 30s | | | |

1. Kịch bản có p95 cao nhất là gì? Dùng số liệu quan sát để giải thích.
2. Endpoint nào tăng failure rate? Phân biệt lỗi HTTP thực và lỗi đánh dấu trong Locust.
3. Với SLO giả định p95 < 300 ms, kịch bản nào đạt? Nêu giới hạn của phép đo.
4. Nếu connection pool bị giới hạn ở 5, bạn sẽ kiểm chứng ảnh hưởng như thế nào?

> Không điền số liệu giả định vào bảng. Không khẳng định hiệu năng production
> từ SQLite + Flask development server trên máy cá nhân.

# Lab 4 — Phân tích kết quả

Đo ngày 2026-11-17 trên máy cá nhân (Windows, Git Bash). Locust và Books API (Flask development server + SQLite `instance/books.db`) chạy **trên cùng một máy**, `-H http://127.0.0.1:5000`. Locustfile: `performance/locustfile.py` (weighted tasks: `GET /books` ×3, `GET /books/{id}` ×2, `search_by_year` ×2, `POST /books` ×1; `wait_time = between(1, 3)`).

Số liệu lấy từ bảng *Request Statistics* / *Response Time Statistics* (dòng **Aggregated**) trong `reports/A.html`, `reports/B.html`, `reports/C.html`.

| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | 18 | 0% (0/143) | 4.9 |
| B | 50 | 5 | 60s | 12 | 0.14% (2/1407) | 23.7 |
| C | 200 | 50 | 30s | 70 | 0.18% (5/2853) | 96.3 |

Chi tiết theo endpoint (p95 ms / số failure / số request):

| Endpoint | A | B | C |
|---|---|---|---|
| `GET /books` | 5 / 0 / 55 | 8 / 0 / 551 | 61 / 0 / 1048 |
| `GET /books/{id}` | 4 / 0 / 28 | 6 / 0 / 356 | 63 / 0 / 723 |
| `GET /books?year=[year]` | 16 / 0 / 35 | 9 / 2 / 333 | 65 / 5 / 708 |
| `POST /books` | 19 / 0 / 25 | 21 / 0 / 167 | 100 / 0 / 374 |
| p99 Aggregated | 19 | 21 | 150 |
| Max | 21 | 51 | 245 |

## 1. Kịch bản có p95 cao nhất

**Kịch bản C (spike)**, p95 = 70 ms, cao gấp khoảng 4–6 lần A (18 ms) và B (12 ms); p99 = 150 ms, max = 245 ms.

Nguyên nhân quan sát được:

- **Spike lúc spawn.** C sinh 50 user/giây, đủ 200 user chỉ sau ~4 giây. Biểu đồ p95 theo thời gian trong `C.html` cho thấy p95 lên **150 ms → 110 ms** ở những mốc đầu, rồi hạ về **~25–30 ms** khi tải ổn định. Như vậy p95 cả lượt chạy bị kéo lên chủ yếu bởi giai đoạn tăng tải đột ngột: request dồn vào server nhanh hơn tốc độ xử lý nên phải xếp hàng.
- **Request ghi chậm nhất.** `POST /books` có p95 cao nhất ở mọi kịch bản (19 → 21 → 100 ms) vì phải ghi và commit vào SQLite; SQLite chỉ cho một writer tại một thời điểm, nên khi tải cao các lệnh ghi phải chờ khoá.
- **A cao hơn B** (18 so với 12 ms) không có nghĩa tải nhẹ chậm hơn: A chỉ có 143 request trong 30 s, nên p95 rơi vào vài request đơn lẻ (request đầu tiên/warm-up, POST). Với mẫu nhỏ, p95 dao động mạnh; B có ~10 lần nhiều mẫu hơn nên ổn định hơn.

RPS tăng gần như tuyến tính theo số user (≈ 0.48 RPS/user ở cả ba kịch bản). Với `wait_time` trung bình 2 s, trần lý thuyết là 0.5 RPS/user, nên **server chưa bão hoà** ở 200 user: thông lượng đang bị giới hạn bởi thời gian chờ của user ảo chứ không phải bởi server.

## 2. Endpoint nào tăng failure rate

Chỉ có **`GET /books?year=[year]`** có failure: 0 (A) → 2/333 = 0.60% (B) → 5/708 = 0.71% (C). Tất cả các endpoint khác 0 failure ở cả ba kịch bản.

**Đây không phải lỗi HTTP thật.** Bảng *Failures* trong `B.html` và `C.html` chỉ có đúng một loại lỗi:

```
CatchResponseError('SIMULATED 500 (client-side response.failure, server returned 200)')
```

Đó là failure **giả lập phía client**: task `search_by_year` gọi `response.failure()` với xác suất 1% trên các response mà server **đã trả 200**. Server không phát ra HTTP 500 nào; bảng *Exceptions* cũng rỗng (không có timeout hay lỗi kết nối).

- Số failure tăng theo số user chỉ vì **số request tăng**; **tỉ lệ** dao động quanh 1% kỳ vọng (0.60%, 0.71%; với A, kỳ vọng chỉ ~0.35 lỗi trên 35 request nên ra 0 là hợp lý). Không có dấu hiệu tỉ lệ lỗi tăng theo tải.
- Cách phân biệt trong report: lỗi giả lập có message bắt đầu bằng `SIMULATED`; lỗi thật từ server sẽ hiện status code thực (`Unexpected status 500`, `503`…) hoặc nằm trong bảng *Exceptions* (`ConnectionError`, timeout).
- `GET /books/{id}` trong locustfile chọn id ngẫu nhiên 1–50, nên một số request trả **404**; locustfile coi 404 là thành công (hành vi đúng của API), vì vậy chúng không bị tính là failure.

## 3. SLO giả định p95 < 300 ms

**Cả ba kịch bản đều đạt** trong phép đo này: p95 Aggregated lần lượt 18 / 12 / 70 ms; ngay cả p99 (150 ms) và max (245 ms) của C cũng dưới 300 ms.

Đề xuất baseline cho CI gate (dựa trên B vì có nhiều mẫu và tải ổn định nhất):

- Chạy kịch bản B (`-u 50 -r 5 -t 60s`) trên cùng một môi trường CI cố định.
- **Fail pipeline nếu:** p95 Aggregated > 300 ms (ngưỡng SLO tuyệt đối), **hoặc** p95 tăng hơn ~50% so với baseline đã lưu của lần chạy trước (bắt regression sớm, khi còn xa ngưỡng SLO), **hoặc** có bất kỳ failure **thật** nào (loại trừ các failure `SIMULATED`).

Giới hạn của phép đo (không thể dùng để khẳng định SLO production):

- Flask **development server** + **SQLite** trên máy cá nhân, không phải WSGI server production (gunicorn/uwsgi) + CSDL thật.
- Locust và API **chạy chung một máy**, tranh CPU với nhau; không có độ trễ mạng thật.
- CSDL nhỏ và `GET /books` chỉ trả tối đa 20 bản ghi/trang, nên truy vấn rất nhẹ.
- Thời gian chạy ngắn (30–60 s): không phát hiện được rò rỉ tài nguyên (cần soak test) hay ngưỡng chịu tải (cần stress test tăng dần user tới khi p95 vỡ).
- Mỗi kịch bản chạy **một lần**; p95 của A dựa trên 143 mẫu nên sai số lớn. Cần chạy lặp lại nhiều lần để có khoảng dao động.
- Percentile của Locust được làm tròn theo bucket, và p95 trong bảng là p95 **cả lượt chạy**, gộp giai đoạn spawn với giai đoạn ổn định.
- SLO này đo **phía server/Locust**, không phải độ trễ người dùng cảm nhận (render client, mạng).

## 4. Nếu connection pool bị giới hạn ở 5

**Dự đoán:** với 200 user đồng thời, mỗi request cần một kết nối CSDL. Khi cả 5 kết nối đều bận, request tiếp theo phải **chờ trong hàng đợi** của pool. Kết quả mong đợi: p95/p99 tăng mạnh (thời gian chờ pool cộng vào latency); nếu thời gian chờ vượt `pool_timeout`, SQLAlchemy ném `TimeoutError` và API trả **HTTP 500 thật**; RPS sẽ ngừng tăng tuyến tính theo số user (bão hoà).

**Kiểm chứng bằng Locust:**

1. Cấu hình pool cố định trong `create_app`, ví dụ `SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 5, "max_overflow": 0, "pool_timeout": 2}`.
2. Chạy lại **cùng** kịch bản C (và B) với cùng locustfile, lưu `reports/C_pool5.html`.
3. So sánh với `C.html`:
   - p95/p99 và biểu đồ response time theo thời gian (đường tăng vọt khi số user vượt ngưỡng);
   - bảng *Failures*: xuất hiện lỗi **thật** `Unexpected status 500` (không có tiền tố `SIMULATED`), tách biệt hoàn toàn với 1% giả lập;
   - RPS: nếu RPS đi ngang trong khi số user vẫn tăng, server đã bão hoà.
4. Để tìm đúng ngưỡng, dùng `LoadTestShape` tăng user theo bậc (10 → 25 → 50 → 100 → 200) và xem p95 bắt đầu tăng phi tuyến ở bậc nào; đối chiếu với log server (`TimeoutError: QueuePool limit of size 5 overflow 0 reached`).
