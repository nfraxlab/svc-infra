"""Tests for svc_infra.api.fastapi.middleware.errors.handlers module."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import Request
from fastapi.responses import JSONResponse

from svc_infra.api.fastapi.middleware.errors.handlers import (
    PROBLEM_MT,
    _json_safe,
    _trace_id_from_request,
    problem_response,
)


class TestTraceIdFromRequest:
    """Tests for _trace_id_from_request function."""

    def test_extracts_x_request_id(self) -> None:
        """Extracts x-request-id header."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"x-request-id": "req-123"}
        result = _trace_id_from_request(mock_request)
        assert result == "req-123"

    def test_extracts_x_correlation_id(self) -> None:
        """Extracts x-correlation-id header."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"x-correlation-id": "corr-456"}
        result = _trace_id_from_request(mock_request)
        assert result == "corr-456"

    def test_extracts_x_trace_id(self) -> None:
        """Extracts x-trace-id header."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"x-trace-id": "trace-789"}
        result = _trace_id_from_request(mock_request)
        assert result == "trace-789"

    def test_returns_none_when_no_headers(self) -> None:
        """Returns None when no trace headers present."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        result = _trace_id_from_request(mock_request)
        assert result is None

    def test_prefers_x_request_id_over_others(self) -> None:
        """Prefers x-request-id over other headers."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {
            "x-request-id": "req-first",
            "x-correlation-id": "corr-second",
        }
        result = _trace_id_from_request(mock_request)
        assert result == "req-first"


class TestJsonSafe:
    """Tests for _json_safe function."""

    def test_primitives_pass_through(self) -> None:
        """Primitive types pass through unchanged."""
        assert _json_safe("string") == "string"
        assert _json_safe(123) == 123
        assert _json_safe(1.5) == 1.5
        assert _json_safe(True) is True
        assert _json_safe(None) is None

    def test_dict_processed_recursively(self) -> None:
        """Dicts are processed recursively."""
        result = _json_safe({"key": "value", "nested": {"inner": 42}})
        assert result == {"key": "value", "nested": {"inner": 42}}

    def test_list_processed_recursively(self) -> None:
        """Lists are processed recursively."""
        result = _json_safe(["a", 1, {"key": "value"}])
        assert result == ["a", 1, {"key": "value"}]

    def test_non_primitives_converted_to_string(self) -> None:
        """Non-primitive types are converted to string."""

        class CustomObj:
            def __str__(self):
                return "custom-obj"

        result = _json_safe(CustomObj())
        assert result == "custom-obj"

    def test_exception_converted_to_string(self) -> None:
        """Exceptions are converted to string."""
        exc = ValueError("test error")
        result = _json_safe(exc)
        assert "test error" in result


class TestProblemResponse:
    """Tests for problem_response function."""

    def test_basic_response(self) -> None:
        """Creates basic problem response."""
        response = problem_response(
            status=400,
            title="Bad Request",
        )
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        assert response.media_type == PROBLEM_MT

    def test_response_with_all_fields(self) -> None:
        """Creates response with all optional fields."""
        response = problem_response(
            status=500,
            title="Internal Server Error",
            detail="Something went wrong",
            type_uri="https://api.example.com/errors/500",
            instance="/api/users/123",
            code="INTERNAL_ERROR",
            errors=[{"field": "email", "message": "invalid"}],
            trace_id="trace-abc",
            headers={"X-Custom": "header"},
        )
        assert response.status_code == 500
        assert response.headers.get("X-Custom") == "header"

    def test_response_body_structure(self) -> None:
        """Response body has correct structure."""
        response = problem_response(
            status=404,
            title="Not Found",
            detail="Resource not found",
            code="NOT_FOUND",
            trace_id="trace-123",
        )
        # Access the body content
        body = response.body
        assert b'"status":404' in body
        assert b'"title":"Not Found"' in body
        assert b'"detail":"Resource not found"' in body
        assert b'"code":"NOT_FOUND"' in body
        assert b'"trace_id":"trace-123"' in body

    def test_type_uri_default(self) -> None:
        """Default type URI is about:blank."""
        response = problem_response(
            status=400,
            title="Bad Request",
        )
        body = response.body
        assert b'"type":"about:blank"' in body

    def test_errors_list_included(self) -> None:
        """Errors list is included in response."""
        response = problem_response(
            status=422,
            title="Validation Error",
            errors=[
                {"loc": ["body", "email"], "msg": "invalid email"},
                {"loc": ["body", "name"], "msg": "required"},
            ],
        )
        body = response.body
        assert b'"errors":' in body


class TestProblemMediaType:
    """Tests for PROBLEM_MT constant."""

    def test_correct_media_type(self) -> None:
        """Media type is application/problem+json."""
        assert PROBLEM_MT == "application/problem+json"


class TestHTTPExceptionHandlerDictDetail:
    """Verify that HTTPException with dict/list detail is preserved, not stringified."""

    def test_dict_detail_preserved_in_json_response(self) -> None:
        """Dict detail is returned as structured JSON, not str(detail)."""
        from fastapi import FastAPI
        from fastapi import HTTPException as _HTTPException
        from fastapi.testclient import TestClient

        from svc_infra.api.fastapi.middleware.errors.handlers import register_error_handlers

        app = FastAPI()
        register_error_handlers(app)

        @app.get("/oauth-502")
        async def oauth_trigger():
            raise _HTTPException(
                status_code=502,
                detail={
                    "error": "Unauthorized",
                    "oauth_supported": True,
                    "authorize_url": "https://github.com/login/oauth/authorize?client_id=abc",
                },
            )

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/oauth-502")
        assert resp.status_code == 502
        body = resp.json()
        # detail must be a dict, not a stringified repr
        assert isinstance(body["detail"], dict)
        assert body["detail"]["oauth_supported"] is True
        assert body["detail"]["authorize_url"].startswith("https://github.com/")

    def test_list_detail_preserved_in_json_response(self) -> None:
        """List detail is returned as structured JSON, not str(detail)."""
        from fastapi import FastAPI
        from fastapi import HTTPException as _HTTPException
        from fastapi.testclient import TestClient

        from svc_infra.api.fastapi.middleware.errors.handlers import register_error_handlers

        app = FastAPI()
        register_error_handlers(app)

        @app.get("/list-detail")
        async def list_trigger():
            raise _HTTPException(status_code=400, detail=[{"field": "email", "error": "required"}])

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/list-detail")
        assert resp.status_code == 400
        body = resp.json()
        assert isinstance(body["detail"], list)
        assert body["detail"][0]["field"] == "email"

    def test_string_detail_uses_problem_json(self) -> None:
        """String detail still returns RFC 7807 problem+json."""
        from fastapi import FastAPI
        from fastapi import HTTPException as _HTTPException
        from fastapi.testclient import TestClient

        from svc_infra.api.fastapi.middleware.errors.handlers import register_error_handlers

        app = FastAPI()
        register_error_handlers(app)

        @app.get("/string-detail")
        async def string_trigger():
            raise _HTTPException(status_code=404, detail="Resource not found")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/string-detail")
        assert resp.status_code == 404
        body = resp.json()
        assert body["detail"] == "Resource not found"
        assert body["title"] == "Not Found"
        assert resp.headers["content-type"].startswith("application/problem+json")
