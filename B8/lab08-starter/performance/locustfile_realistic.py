"""Optional stateful flow (slide 29); does not require production auth."""
import itertools
from locust import HttpUser, between, task

_counter = itertools.count(1)


class BuyerUser(HttpUser):
    wait_time = between(2, 5)

    def on_start(self):
        res = self.client.post(
            "/auth/login", json={"user": "lab", "pwd": "lab"},
            name="POST /auth/login (demo)",
        )
        self.token = res.json().get("token") if res.ok else None

    @task(3)
    def browse(self):
        self.client.get("/books", name="GET /books")

    @task(1)
    def create_and_delete(self):
        if not self.token:
            return
        unique = next(_counter)
        response = self.client.post(
            "/books", json={"title": f"Buyer {unique}", "author": "lab"},
            name="POST /books",
        )
        if response.status_code == 201:
            book_id = response.json()["id"]
            self.client.delete(f"/books/{book_id}", name="DELETE /books/{id}")
