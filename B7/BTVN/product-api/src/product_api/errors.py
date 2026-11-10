from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Base — mọi lỗi nghiệp vụ kế thừa class này."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message="", code=None, status=None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status:
            self.status_code = status


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class OutOfStock(ApiError):
    status_code = 409
    code = "out_of_stock"


def register_error_handlers(app):
    # Định dạng lỗi theo yêu cầu Lab 1: {"error": "...", "detail": "..."}

    @app.errorhandler(ApiError)
    def _on_api_error(err):
        return jsonify(error=err.code, detail=err.message), err.status_code

    @app.errorhandler(ValidationError)
    def _on_validation_error(err):
        return jsonify(error="validation_error", detail=err.messages), 422

    @app.errorhandler(HTTPException)
    def _on_http_error(err):
        return (
            jsonify(error=err.name.lower().replace(" ", "_"), detail=err.description),
            err.code,
        )

    @app.errorhandler(Exception)
    def _on_unhandled(err):
        app.logger.exception("unhandled error")
        return jsonify(error="internal_error", detail="unexpected error"), 500
