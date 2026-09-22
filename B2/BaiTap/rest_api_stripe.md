# Báo Cáo Audit REST API: Hệ Thống Stripe

Tài liệu này thực hiện đánh giá, phân tích tính tuân thủ kiến trúc RESTful trên 5 endpoint đại diện của hệ sinh thái **Stripe API** (một trong những chuẩn mực thiết kế API thanh toán phổ biến nhất thế giới).

---

## 1. Thông Tin Tổng Quan Hệ Thống

* **Base URL:** `https://api.stripe.com/v1`
* **Định dạng dữ liệu:** 
  * Gửi lên (Request Body): `application/x-www-form-urlencoded`
  * Trả về (Response Body): `application/json`
* **Cơ chế xác thực (Authentication):** HTTP Basic Auth với Secret API Key (`Authorization: Bearer sk_test_...`)
* **Đặc trưng kiến trúc:** Sử dụng phong cách **Pragmatic REST** (REST thực tế), tập trung vào tính tương thích cao và đảm bảo tính toàn vẹn dữ liệu giao dịch bằng cơ chế Idempotency.

---

## 2. Bảng Tổng Hợp 5 Endpoints Được Audit

| # | Endpoint | HTTP Method | Status Codes | Headers Quan Trọng | Đánh Giá RESTful |
|---|---|---|---|---|---|
| **1** | `/customers/{customer_id}` | `GET` | `200`, `404` | `Stripe-Version`, `Request-Id` | **Chuẩn REST** |
| **2** | `/customers` | `POST` | `200`, `400`, `401` | `Idempotency-Key`, `Idempotent-Replayed` | **Pragmatic REST** |
| **3** | `/customers/{customer_id}` | `POST` | `200`, `404` | `Request-Id`, `Idempotency-Key` | **Semi-RESTful** |
| **4** | `/subscriptions/{subscription_id}` | `DELETE` | `200`, `404` | `Idempotency-Key`, `Request-Id` | **Chuẩn REST** |
| **5** | `/transfers/{transfer_id}/reversals` | `POST` | `200`, `400` | `Idempotency-Key`, `Request-Id` | **Chuẩn REST (Sub-resource)** |

---

## 3. Phân Tích Chi Tiết Từng Endpoint

### 3.1. Truy vấn thông tin khách hàng (Retrieve Customer)

* **URL:** `GET /customers/{customer_id}`
* **Mục đích:** Đọc dữ liệu chi tiết của một đối tượng khách hàng theo mã định danh.
* **HTTP Status Codes:**
  * `200 OK`: Truy vấn thành công, trả về JSON biểu diễn Customer Object.
  * `404 Not Found`: Mã khách hàng không tồn tại trên hệ thống.
* **Headers quan trọng:**
  * **Request:** 
    * `Authorization: Bearer <SECRET_KEY>`
    * `Stripe-Version: YYYY-MM-DD` *(Khóa phiên bản API schema cụ thể)*
  * **Response:**
    * `Request-Id`: Mã định danh trace log của request.
    * `Content-Type: application/json`
* **Đánh giá tính RESTful:** **Tuân thủ chuẩn REST hoàn toàn**.
  * Định danh tài nguyên chuẩn bằng danh từ số nhiều `/customers` kết hợp ID cụ thể.
  * Thao tác có tính chất **Safe** (không làm biến đổi dữ liệu) và **Idempotent**.

---

### 3.2. Tạo mới một khách hàng (Create Customer)

* **URL:** `POST /customers`
* **Mục đích:** Thêm một bản ghi khách hàng mới vào hệ thống.
* **HTTP Status Codes:**
  * `200 OK`: Tạo mới thành công, trả về thông tin đối tượng vừa tạo.
  * `400 Bad Request`: Thiếu tham số bắt buộc hoặc định dạng email/thông tin sai.
  * `401 Unauthorized`: API Key không hợp lệ.
* **Headers quan trọng:**
  * **Request:**
    * `Content-Type: application/x-www-form-urlencoded`
    * `Idempotency-Key: <UUID>` *(Header trọng yếu chống trùng lặp dữ liệu)*
  * **Response:**
    * `Idempotent-Replayed: true/false` *(Báo hiệu kết quả này là tính toán mới hay lấy từ cache do gửi lặp request)*
* **Đánh giá tính RESTful:** **Pragmatic REST (REST thực dụng)**.
  * Điểm chuẩn: Sử dụng đúng HTTP Method `POST` gửi vào URI tập hợp tài nguyên (`/customers`).
  * Điểm khác biệt lý thuyết: Trả về mã `200 OK` thay vì mã `201 Created`. Stripe lựa chọn mã này để tối ưu hóa việc phân tích phản hồi đồng nhất ở phía client SDK.

---

### 3.3. Cập nhật thông tin khách hàng (Update Customer)

* **URL:** `POST /customers/{customer_id}`
* **Mục đích:** Cập nhật một số trường (partial update) như email, name, metadata của khách hàng.
* **HTTP Status Codes:**
  * `200 OK`: Cập nhật thành công, trả về thông tin khách hàng mới nhất.
  * `404 Not Found`: Không tìm thấy ID khách hàng cần cập nhật.
* **Headers quan trọng:**
  * **Request:** `Authorization: Bearer <SECRET_KEY>`, `Idempotency-Key`
  * **Response:** `Request-Id`
* **Đánh giá tính RESTful:** **Semi-RESTful**.
  * *Lý thuyết REST thuần:* Thao tác cập nhật từng phần phải sử dụng `PATCH`, hoặc cập nhật toàn bộ (thay thế) phải dùng `PUT`.
  * *Thực tế của Stripe:* Stripe dùng hoàn toàn `POST` cho cả việc tạo và sửa để tương thích tốt với các thư viện HTTP client cũ không hỗ trợ đầy đủ `PATCH`.

---

### 3.4. Hủy một gói thuê bao (Cancel Subscription)

* **URL:** `DELETE /subscriptions/{subscription_id}`
* **Mục đích:** Đóng/hủy một hợp đồng đăng ký dịch vụ định kỳ.
* **HTTP Status Codes:**
  * `200 OK`: Hủy gói thành công, trả về object subscription với thuộc tính `"status": "canceled"`.
  * `404 Not Found`: Không tìm thấy subscription tương ứng.
* **Headers quan trọng:**
  * **Request:** `Authorization: Bearer <SECRET_KEY>`, `Idempotency-Key`
  * **Response:** `Content-Type: application/json`
* **Đánh giá tính RESTful:** **Tuân thủ chuẩn REST**.
  * Sử dụng chuẩn động từ `DELETE` cho hành vi xóa/chấm dứt tài nguyên.
  * Thay vì trả về `204 No Content` (không có thân phản hồi), Stripe trả về `200 OK` kèm object cập nhật giúp client đồng bộ trạng thái giao diện ngay lập tức mà không cần gọi thêm một request `GET`.

---

### 3.5. Đảo ngược / Thu hồi chuyển khoản (Reverse a Transfer)

* **URL:** `POST /transfers/{transfer_id}/reversals`
* **Mục đích:** Khởi tạo yêu cầu hoàn trả/thu hồi một khoản tiền chuyển khoản trước đó.
* **HTTP Status Codes:**
  * `200 OK`: Lệnh hoàn trả được tạo thành công.
  * `400 Bad Request`: Số tiền yêu cầu hoàn vượt quá số dư chuyển khoản gốc.
* **Headers quan trọng:**
  * **Request:** `Idempotency-Key: <UUID>`, `Authorization: Bearer <SECRET_KEY>`
  * **Response:** `Request-Id`
* **Đánh giá tính RESTful:** **Tuân thủ chuẩn REST ở mức cao (Sub-resource Modeling)**.
  * Bài học chuẩn mực về xử lý nghiệp vụ: Chuyển một hành động (động từ "reverse") thành một danh từ tài nguyên (`reversals`).
  * Thể hiện mối quan hệ cha - con phân cấp: Một bản ghi `reversal` là tài nguyên con gắn chặt với tài nguyên cha là `transfers/{id}`.

---

## 4. Kết Luận Chung Về Kiến Trúc

Hệ sinh thái Stripe API minh chứng cho phong cách thiết kế **Pragmatic RESTful**:
1. **Ưu tiên độ tin cậy trong giao dịch:** Ứng dụng header `Idempotency-Key` giải quyết bài toán cốt lõi của thanh toán phân tán (tránh trừ tiền 2 lần khi mất kết nối mạng).
2. **Quản lý phiên bản chặt chẽ:** Sử dụng Header `Stripe-Version` thay vì phân nhánh URL (`/v1/`, `/v2/`), cho phép người dùng khóa chết phiên bản dữ liệu an toàn.
3. **Thực dụng hơn giáo điều:** Chấp nhận dùng `POST` thay vì `PATCH` và ưu tiên trả về `200 OK` kèm dữ liệu thay vì `204 No Content` hay `201 Created` nhằm tối đa hóa tính tương thích và tiện lợi cho lập trình viên tích hợp.