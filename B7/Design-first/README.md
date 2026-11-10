# Design-First — connexion

Viết OpenAPI spec **trước** (`openapi/products.yaml`), connexion đọc spec để tạo route,
validate request/response, rồi gọi hàm Python có tên trùng `operationId`.

```
openapi.yaml → routes + schema → handler logic
```

## Chạy

```bash
python -m venv .venv
source .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- Swagger UI: http://localhost:8080/ui
- Spec: http://localhost:8080/openapi.json

## Endpoints

| Method | Path | operationId | Kết quả |
|---|---|---|---|
| GET | /products | api.products.list_products | 200 |
| POST | /products | api.products.create_product | 201 · 400 body sai spec · 409 trùng sku |
| GET | /products/{id} | api.products.get_product | 200 · 404 |

## File

- `openapi/products.yaml` — hợp đồng API, là nguồn gốc duy nhất
- `api/products.py` — handler, tên hàm trùng `operationId`
- `app.py` — `connexion.FlaskApp` + `add_api(...)` nối spec với handler
