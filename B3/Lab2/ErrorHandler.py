import logging
from flask import Flask, Response, json, request
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ==========================================================
# 1. Định nghĩa Custom Exception class: ProblemError
# ==========================================================
class ProblemError(Exception):
    def __init__(self, status=400, title=None, detail=None, type_uri="about:blank", instance=None, extra=None):
        super().__init__(detail or title)
        self.status = status
        self.title = title or "Bad Request"
        self.detail = detail
        self.type_uri = type_uri
        self.instance = instance
        self.extra = extra or {}

    def to_dict(self):
        payload = {
            "type": self.type_uri,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance or request.path,
        }
        if self.extra:
            payload.update(self.extra)
        return payload


def make_problem_response(data, status_code):
    """Tạo response chuẩn MIME type application/problem+json"""
    return Response(
        response=json.dumps(data, ensure_ascii=False),
        status=status_code,
        mimetype="application/problem+json"
    )


# ==========================================================
# 2. Handler cho custom exception ProblemError
# ==========================================================
@app.errorhandler(ProblemError)
def handle_problem_error(error):
    return make_problem_response(error.to_dict(), error.status)


# ==========================================================
# 3. Handler fallback cho HTTPException (404, 405, 400 mặc định...)
# ==========================================================
@app.errorhandler(HTTPException)
def handle_http_exception(error):
    payload = {
        "type": "about:blank",
        "title": error.name,
        "status": error.code,
        "detail": error.description,
        "instance": request.path,
    }
    return make_problem_response(payload, error.code)


# ==========================================================
# 4. Handler fallback cho lỗi không bắt được (500 Internal Error)
# ==========================================================
@app.errorhandler(Exception)
def handle_unexpected_exception(error):
    # Log chi tiết stack trace ở phía server để debug
    app.logger.exception("Lỗi không mong muốn: %s", error)

    # Trả về message trung tính, tuyệt đối không lộ stack trace cho client
    payload = {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "Đã xảy ra sự cố nội bộ trên máy chủ. Vui lòng thử lại sau.",
        "instance": request.path,
    }
    return make_problem_response(payload, 500)


# ==========================================================
# Các route demo kiểm thử theo yêu cầu
# ==========================================================

# Mock database
RESOURCES = {
    1: {"id": 1, "name": "Resource mẫu 1"}
}

# Kiểm thử 1: Request tới /resources/{id}
@app.route("/resources/<int:resource_id>", methods=["GET"])
def get_resource(resource_id):
    item = RESOURCES.get(resource_id)
    if not item:
        # Bắn lỗi 404 tùy biến với ProblemError
        raise ProblemError(
            status=404,
            title="Resource Not Found",
            detail=f"Không tìm thấy resource với id '{resource_id}'.",
            type_uri="https://example.com/errors/not-found"
        )
    return item, 200

# Kiểm thử 2: Route cố tình gây lỗi 500 unhandled
@app.route("/crash", methods=["GET"])
def trigger_crash():
    _ = 1 / 0  # ZeroDivisionError
    return {"message": "ok"}


if __name__ == "__main__":
    app.run(debug=False)