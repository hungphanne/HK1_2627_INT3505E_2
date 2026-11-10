# Product API — SOA Buổi 7

Flask + SQLAlchemy 2.x + marshmallow + Flask-Migrate, đóng gói Docker.

## Chạy local (SQLite)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
flask --app product_api.factory db upgrade
flask --app product_api.factory run --debug
```

## Chạy test

```bash
pytest -v
```

## Chạy bằng Docker (PostgreSQL)

```bash
docker compose up --build
```

## Endpoints

| Method | Path | Mô tả |
|---|---|---|
| GET | /api/v1/products?page=1&size=20 | Danh sách có phân trang (loại archived) |
| GET | /api/v1/products/{id} | 1 sản phẩm, 404 nếu không có/đã archived |
| POST | /api/v1/products | Tạo, 409 nếu trùng sku, 422 nếu sai dữ liệu |
| POST | /api/v1/products/{id}/reserve | Body `{"qty": n}`, 409 nếu hết hàng |
| PATCH | /api/v1/products/{id} | Cập nhật một phần |
| DELETE | /api/v1/products/{id} | Soft delete (archived=true), 204 |
| POST | /api/v1/orders | Tạo đơn nhiều sản phẩm (OrderItem), trừ kho atomic |
| GET | /api/v1/orders | Danh sách đơn (eager loading, không N+1) |
| GET | /api/v1/orders/{id} | Chi tiết đơn |
| GET | /healthz | Liveness — không chạm DB |
| GET | /ready | Readiness — kiểm tra DB, 503 nếu lỗi |

Lỗi trả về dạng `{"error": "<code>", "detail": "<message>"}`.
