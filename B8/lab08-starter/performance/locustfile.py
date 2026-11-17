"""Lab 4: weighted tasks, optional 404, no deliberate server errors.

search_by_year có 1% failure giả lập phía client (Locust response.failure()),
KHÔNG phải HTTP 500 do server phát.

Run: locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 \
         -u 10 -r 2 -t 30s --html reports/A.html
"""
import itertools
import random

from locust import HttpUser, between, task

_counter = itertools.count(1)
SIMULATED_FAILURE_RATE = 0.01  # 1% — giả lập ở phía Locust, không phải lỗi server


class BooksUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_books(self):
        self.client.get("/books", name="GET /books")

    @task(2)
    def read_book(self):
        book_id = random.randint(1, 50)
        with self.client.get(
            f"/books/{book_id}", name="GET /books/{id}", catch_response=True
        ) as response:
            # Expected 404 (random id absent) is not an operational failure.
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def create_book(self):
        unique = next(_counter)
        self.client.post(
            "/books",
            json={"title": f"Load test {unique}", "author": "locust"},
            name="POST /books",
        )

    # LAB 4: search_by_year với 1% failure giả lập.
    #
    # Failure này là CLIENT-SIDE: Locust gọi response.failure() trên một response
    # mà server thực ra đã trả 200. Server KHÔNG phát HTTP 500 nào.
    # Trong report, các failure này có message bắt đầu bằng "SIMULATED"; còn lỗi
    # thật từ server (5xx, timeout, connection error) giữ nguyên status code
    # → đọc bảng Failures trong report HTML để phân biệt hai loại.
    @task(2)
    def search_by_year(self):
        year = random.randint(1990, 2025)
        with self.client.get(
            f"/books?year={year}", name="GET /books?year=[year]", catch_response=True
        ) as response:
            if response.status_code != 200:
                # Lỗi thật từ server (hoặc mạng) — không phải lỗi giả lập.
                response.failure(f"Unexpected status {response.status_code}")
            elif random.random() < SIMULATED_FAILURE_RATE:
                response.failure(
                    "SIMULATED 500 (client-side response.failure, server returned 200)"
                )
            else:
                response.success()