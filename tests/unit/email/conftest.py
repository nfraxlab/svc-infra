"""Fixtures for email tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def clean_email_environment() -> None:
    """Clear email-related environment variables and caches before each test.

    This ensures tests run in isolation without interference from CI
    environment variables or cached settings from previous tests.
    """
    # Store original values to restore after test
    original_env = {}
    email_keys = [k for k in os.environ.keys() if k.startswith("EMAIL_")]
    for key in email_keys:
        original_env[key] = os.environ.pop(key)

    # Also clear AWS_ACCESS_KEY_ID if set (triggers SES detection)
    aws_key = os.environ.pop("AWS_ACCESS_KEY_ID", None)

    # Clear settings cache
    from svc_infra.email.settings import get_email_settings

    get_email_settings.cache_clear()

    # Clear add module state
    import svc_infra.email.add as add_module

    add_module._app_email_backend = None
    add_module._app_email_sender = None

    yield

    # Restore original environment
    for key, value in original_env.items():
        os.environ[key] = value
    if aws_key:
        os.environ["AWS_ACCESS_KEY_ID"] = aws_key

    # Clear cache again after test
    get_email_settings.cache_clear()
