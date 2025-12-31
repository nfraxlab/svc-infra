"""Tests for svc_infra.api.fastapi.middleware.errors.exceptions module."""

from __future__ import annotations

import pytest

from svc_infra.api.fastapi.middleware.errors.exceptions import FastApiException


class TestFastApiExceptionInit:
    """Tests for FastApiException initialization."""

    def test_title_is_required(self) -> None:
        """Title should be required."""
        exc = FastApiException(title="Bad Request")
        assert exc.title == "Bad Request"

    def test_default_status_code_is_400(self) -> None:
        """Default status code should be 400."""
        exc = FastApiException(title="Error")
        assert exc.status_code == 400

    def test_custom_status_code(self) -> None:
        """Should accept custom status code."""
        exc = FastApiException(title="Not Found", status_code=404)
        assert exc.status_code == 404

    def test_detail_default_is_none(self) -> None:
        """Detail should default to None."""
        exc = FastApiException(title="Error")
        assert exc.detail is None

    def test_custom_detail(self) -> None:
        """Should accept custom detail."""
        exc = FastApiException(title="Error", detail="Something went wrong")
        assert exc.detail == "Something went wrong"


class TestFastApiExceptionCode:
    """Tests for FastApiException code generation."""

    def test_auto_generates_code_from_title(self) -> None:
        """Should auto-generate code from title."""
        exc = FastApiException(title="Bad Request")
        assert exc.code == "BAD_REQUEST"

    def test_code_replaces_spaces(self) -> None:
        """Code should replace spaces with underscores."""
        exc = FastApiException(title="Invalid User Input")
        assert exc.code == "INVALID_USER_INPUT"

    def test_code_is_uppercase(self) -> None:
        """Code should be uppercase."""
        exc = FastApiException(title="lowercase title")
        assert exc.code == "LOWERCASE_TITLE"

    def test_custom_code(self) -> None:
        """Should accept custom code."""
        exc = FastApiException(title="Error", code="CUSTOM_CODE")
        assert exc.code == "CUSTOM_CODE"

    def test_custom_code_overrides_auto(self) -> None:
        """Custom code should override auto-generated code."""
        exc = FastApiException(title="Bad Request", code="MY_ERROR")
        assert exc.code == "MY_ERROR"


class TestFastApiExceptionInheritance:
    """Tests for FastApiException inheritance."""

    def test_inherits_from_exception(self) -> None:
        """Should inherit from Exception."""
        assert issubclass(FastApiException, Exception)

    def test_can_be_raised(self) -> None:
        """Should be raisable."""
        with pytest.raises(FastApiException):
            raise FastApiException(title="Test Error")

    def test_can_be_caught_as_exception(self) -> None:
        """Should be catchable as Exception."""
        with pytest.raises(FastApiException):
            raise FastApiException(title="Test Error")


class TestFastApiExceptionStatusCodes:
    """Tests for common HTTP status codes."""

    def test_400_bad_request(self) -> None:
        """Should work for 400 Bad Request."""
        exc = FastApiException(title="Bad Request", status_code=400)
        assert exc.status_code == 400

    def test_401_unauthorized(self) -> None:
        """Should work for 401 Unauthorized."""
        exc = FastApiException(title="Unauthorized", status_code=401)
        assert exc.status_code == 401

    def test_403_forbidden(self) -> None:
        """Should work for 403 Forbidden."""
        exc = FastApiException(title="Forbidden", status_code=403)
        assert exc.status_code == 403

    def test_404_not_found(self) -> None:
        """Should work for 404 Not Found."""
        exc = FastApiException(title="Not Found", status_code=404)
        assert exc.status_code == 404

    def test_409_conflict(self) -> None:
        """Should work for 409 Conflict."""
        exc = FastApiException(title="Conflict", status_code=409)
        assert exc.status_code == 409

    def test_422_unprocessable_entity(self) -> None:
        """Should work for 422 Unprocessable Entity."""
        exc = FastApiException(title="Validation Error", status_code=422)
        assert exc.status_code == 422

    def test_500_internal_error(self) -> None:
        """Should work for 500 Internal Server Error."""
        exc = FastApiException(title="Internal Error", status_code=500)
        assert exc.status_code == 500


class TestFastApiExceptionUsage:
    """Tests for real-world usage patterns."""

    def test_with_all_parameters(self) -> None:
        """Should work with all parameters."""
        exc = FastApiException(
            title="Validation Failed",
            detail="Field 'email' is required",
            status_code=422,
            code="VALIDATION_FAILED",
        )
        assert exc.title == "Validation Failed"
        assert exc.detail == "Field 'email' is required"
        assert exc.status_code == 422
        assert exc.code == "VALIDATION_FAILED"

    def test_access_attributes(self) -> None:
        """Should be able to access all attributes."""
        exc = FastApiException(title="Error", detail="Details", status_code=400)
        assert hasattr(exc, "title")
        assert hasattr(exc, "detail")
        assert hasattr(exc, "status_code")
        assert hasattr(exc, "code")
