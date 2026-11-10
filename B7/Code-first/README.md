# Code-First — flask-smorest

Viết code (MethodView + marshmallow Schema) trước, OpenAPI **tự sinh** từ code.

```
code (Flask) → spec / doc → Swagger UI
```

## Chạy

```bash
python -m venv .venv
source .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- Swagger UI: http://localhost:5001/swagger-ui
- OpenAPI sinh tự động: http://localhost:5001/openapi.json

## Endpoints

| Method | Path | Kết quả |
|---|---|---|
| GET | /products | 200 danh sách |
| POST | /products | 201 tạo mới · 409 trùng sku · 422 body sai |
| GET | /products/{id} | 200 · 404 |

## File

- `schemas.py` — marshmallow Schema: vừa validate/serialize, vừa là nguồn sinh OpenAPI
- `products.py` — Blueprint + MethodView, decorator `@blp.arguments` / `@blp.response`
- `app.py` — cấu hình `API_TITLE`, `OPENAPI_*` và đăng ký blueprint vào `Api`
