"""Coverage tests for utils module and http client.

Targets:
- utils.py: deprecated decorator, deprecated_parameter, write, ensure_init_py
- http/client.py: set_request_id, get_request_id, parse_float_env
"""

from __future__ import annotations

import os
import tempfile
import warnings
from pathlib import Path
from unittest.mock import patch

import httpx

from svc_infra.http.client import (
    _merge_request_id_header,
    _parse_float_env,
    get_default_timeout_seconds,
    get_request_id,
    make_timeout,
    new_async_httpx_client,
    new_httpx_client,
    set_request_id,
)
from svc_infra.utils import (
    DeprecatedWarning,
    deprecated,
    deprecated_parameter,
    ensure_init_py,
    write,
)

# ============== HTTP Client Tests ==============


class TestRequestIdContext:
    def test_set_and_get_request_id(self) -> None:
        set_request_id("test-request-123")
        assert get_request_id() == "test-request-123"
        set_request_id(None)
        assert get_request_id() is None

    def test_merge_request_id_header_with_id(self) -> None:
        set_request_id("req-456")
        result = _merge_request_id_header({"Content-Type": "application/json"})
        assert result["X-Request-Id"] == "req-456"
        assert result["Content-Type"] == "application/json"
        set_request_id(None)

    def test_merge_request_id_header_without_id(self) -> None:
        set_request_id(None)
        result = _merge_request_id_header({"Content-Type": "text/plain"})
        assert "X-Request-Id" not in result
        assert result["Content-Type"] == "text/plain"

    def test_merge_request_id_header_none_headers(self) -> None:
        set_request_id("req-789")
        result = _merge_request_id_header(None)
        assert result["X-Request-Id"] == "req-789"
        set_request_id(None)

    def test_merge_request_id_header_existing_id(self) -> None:
        set_request_id("new-id")
        # Existing X-Request-Id should not be overwritten
        result = _merge_request_id_header({"X-Request-Id": "existing-id"})
        assert result["X-Request-Id"] == "existing-id"
        set_request_id(None)


class TestParseFloatEnv:
    def test_parse_float_env_not_set(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TEST_FLOAT_VAR", None)
            result = _parse_float_env("TEST_FLOAT_VAR", 5.0)
            assert result == 5.0

    def test_parse_float_env_empty_string(self) -> None:
        with patch.dict(os.environ, {"TEST_FLOAT_VAR": ""}):
            result = _parse_float_env("TEST_FLOAT_VAR", 5.0)
            assert result == 5.0

    def test_parse_float_env_valid_float(self) -> None:
        with patch.dict(os.environ, {"TEST_FLOAT_VAR": "15.5"}):
            result = _parse_float_env("TEST_FLOAT_VAR", 5.0)
            assert result == 15.5

    def test_parse_float_env_invalid(self) -> None:
        with patch.dict(os.environ, {"TEST_FLOAT_VAR": "not-a-float"}):
            result = _parse_float_env("TEST_FLOAT_VAR", 5.0)
            assert result == 5.0


class TestGetDefaultTimeoutSeconds:
    def test_get_default_timeout_from_env(self) -> None:
        with patch.dict(os.environ, {"HTTP_CLIENT_TIMEOUT_SECONDS": "30.0"}):
            result = get_default_timeout_seconds()
            assert result == 30.0

    def test_get_default_timeout_fallback(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HTTP_CLIENT_TIMEOUT_SECONDS", None)
            result = get_default_timeout_seconds()
            assert result == 10.0


class TestMakeTimeout:
    def test_make_timeout_with_seconds(self) -> None:
        timeout = make_timeout(20.0)
        assert isinstance(timeout, httpx.Timeout)

    def test_make_timeout_default(self) -> None:
        timeout = make_timeout(None)
        assert isinstance(timeout, httpx.Timeout)


class TestNewHttpxClient:
    def test_new_httpx_client_default(self) -> None:
        client = new_httpx_client()
        assert isinstance(client, httpx.Client)
        client.close()

    def test_new_httpx_client_with_timeout(self) -> None:
        client = new_httpx_client(timeout_seconds=30.0)
        assert isinstance(client, httpx.Client)
        client.close()

    def test_new_httpx_client_with_headers(self) -> None:
        client = new_httpx_client(headers={"X-Custom": "value"})
        assert isinstance(client, httpx.Client)
        client.close()

    def test_new_httpx_client_with_base_url(self) -> None:
        client = new_httpx_client(base_url="https://example.com")
        assert isinstance(client, httpx.Client)
        client.close()

    def test_new_httpx_client_no_request_id_propagation(self) -> None:
        set_request_id("test-id")
        client = new_httpx_client(propagate_request_id=False)
        assert isinstance(client, httpx.Client)
        client.close()
        set_request_id(None)

    def test_new_httpx_client_with_request_id(self) -> None:
        set_request_id("test-request-id")
        client = new_httpx_client(headers={"Other": "header"})
        assert isinstance(client, httpx.Client)
        client.close()
        set_request_id(None)


class TestNewAsyncHttpxClient:
    def test_new_async_httpx_client_default(self) -> None:
        client = new_async_httpx_client()
        assert isinstance(client, httpx.AsyncClient)

    def test_new_async_httpx_client_with_timeout(self) -> None:
        client = new_async_httpx_client(timeout_seconds=15.0)
        assert isinstance(client, httpx.AsyncClient)

    def test_new_async_httpx_client_with_base_url(self) -> None:
        client = new_async_httpx_client(base_url="https://api.example.com")
        assert isinstance(client, httpx.AsyncClient)

    def test_new_async_httpx_client_no_request_id_propagation(self) -> None:
        set_request_id("async-test-id")
        client = new_async_httpx_client(propagate_request_id=False)
        assert isinstance(client, httpx.AsyncClient)
        set_request_id(None)


# ============== Utils Tests ==============


class TestWrite:
    def test_write_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            result = write(path, "hello world")
            assert result["action"] == "wrote"
            assert path.read_text() == "hello world"

    def test_write_creates_parent_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dir" / "test.txt"
            result = write(path, "content")
            assert result["action"] == "wrote"
            assert path.exists()

    def test_write_skips_existing_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "existing.txt"
            path.write_text("original")
            result = write(path, "new content", overwrite=False)
            assert result["action"] == "skipped"
            assert result["reason"] == "exists"
            assert path.read_text() == "original"

    def test_write_overwrites_with_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "existing.txt"
            path.write_text("original")
            result = write(path, "new content", overwrite=True)
            assert result["action"] == "wrote"
            assert path.read_text() == "new content"


class TestEnsureInitPy:
    def test_ensure_init_py_basic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dir_path = Path(tmpdir) / "package"
            dir_path.mkdir()
            result = ensure_init_py(dir_path, False, False, "# init")
            assert result["action"] == "wrote"
            assert (dir_path / "__init__.py").read_text() == "# init"


class TestDeprecatedWarning:
    def test_deprecated_warning_is_deprecation_warning(self) -> None:
        assert issubclass(DeprecatedWarning, DeprecationWarning)


class TestDeprecatedDecorator:
    def test_deprecated_function(self) -> None:
        @deprecated(version="1.0.0", reason="Use new_func instead")
        def old_func() -> str:
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_func()
            assert result == "result"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecatedWarning)
            assert "deprecated since version 1.0.0" in str(w[0].message)
            assert "Use new_func instead" in str(w[0].message)

    def test_deprecated_function_with_removal_version(self) -> None:
        @deprecated(version="1.0.0", reason="Use new_func", removal_version="2.0.0")
        def old_func() -> str:
            return "value"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            old_func()
            assert len(w) == 1
            assert "removed in version 2.0.0" in str(w[0].message)

    def test_deprecated_class(self) -> None:
        @deprecated(version="1.0.0", reason="Use NewClass instead")
        class OldClass:
            def __init__(self) -> None:
                self.value = 42

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            instance = OldClass()
            assert instance.value == 42
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecatedWarning)

    def test_deprecated_preserves_docstring(self) -> None:
        @deprecated(version="1.0.0", reason="Deprecated")
        def documented_func() -> None:
            """Original docstring."""
            pass

        assert "Original docstring" in (documented_func.__doc__ or "")
        assert "deprecated" in (documented_func.__doc__ or "")

    def test_deprecated_class_preserves_docstring(self) -> None:
        @deprecated(version="1.0.0", reason="Deprecated")
        class DocumentedClass:
            """Original class docstring."""

            pass

        assert "Original class docstring" in (DocumentedClass.__doc__ or "")
        assert "deprecated" in (DocumentedClass.__doc__ or "")

    def test_deprecated_class_no_docstring(self) -> None:
        @deprecated(version="1.0.0", reason="Deprecated")
        class NoDocClass:
            pass

        assert "deprecated" in (NoDocClass.__doc__ or "")

    def test_deprecated_function_no_docstring(self) -> None:
        @deprecated(version="1.0.0", reason="Deprecated")
        def no_doc_func() -> None:
            pass

        assert "deprecated" in (no_doc_func.__doc__ or "")


class TestDeprecatedParameter:
    def test_deprecated_parameter_warning(self) -> None:
        def func_with_deprecated_param(new_param: str, old_param: str | None = None) -> str:
            if old_param is not None:
                deprecated_parameter(
                    name="old_param",
                    version="1.0.0",
                    reason="Use new_param instead",
                )
                new_param = old_param
            return new_param

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = func_with_deprecated_param("test", old_param="old_value")
            assert result == "old_value"
            assert len(w) == 1
            assert "old_param" in str(w[0].message)
            assert "deprecated since version 1.0.0" in str(w[0].message)

    def test_deprecated_parameter_with_removal_version(self) -> None:
        def func() -> None:
            deprecated_parameter(
                name="param",
                version="1.0.0",
                reason="Use new_param",
                removal_version="2.0.0",
            )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            func()
            assert len(w) == 1
            assert "removed in version 2.0.0" in str(w[0].message)
