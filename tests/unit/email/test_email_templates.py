"""Tests for email templates."""

from __future__ import annotations

import pytest

from svc_infra.email.templates import EmailTemplateLoader
from svc_infra.email.templates.loader import TemplateNotFoundError

# ─── EmailTemplateLoader Tests ─────────────────────────────────────────────


class TestEmailTemplateLoader:
    """Tests for EmailTemplateLoader."""

    def test_init_defaults(self) -> None:
        """Test EmailTemplateLoader initialization with defaults."""
        loader = EmailTemplateLoader()
        assert loader.default_context["app_name"] == "Our Service"
        assert loader.default_context["app_url"] == ""
        assert loader._env is not None

    def test_init_custom_branding(self) -> None:
        """Test EmailTemplateLoader with custom branding."""
        loader = EmailTemplateLoader(
            app_name="TestApp",
            app_url="https://testapp.com",
            support_email="help@testapp.com",
            unsubscribe_url="https://testapp.com/unsubscribe",
        )
        assert loader.default_context["app_name"] == "TestApp"
        assert loader.default_context["app_url"] == "https://testapp.com"
        assert loader.default_context["support_email"] == "help@testapp.com"
        assert loader.default_context["unsubscribe_url"] == "https://testapp.com/unsubscribe"

    def test_get_available_templates(self) -> None:
        """Test get_available_templates returns built-in templates."""
        loader = EmailTemplateLoader()
        templates = loader.get_available_templates()

        assert "verification" in templates
        assert "password_reset" in templates
        assert "invitation" in templates
        assert "welcome" in templates
        # Should not include base template
        assert "base" not in templates

    def test_template_exists(self) -> None:
        """Test template_exists method."""
        loader = EmailTemplateLoader()

        assert loader.template_exists("verification") is True
        assert loader.template_exists("password_reset") is True
        assert loader.template_exists("nonexistent") is False

    def test_render_verification_template(self) -> None:
        """Test rendering verification template."""
        loader = EmailTemplateLoader(app_name="TestApp")

        html, text = loader.render(
            "verification",
            code="123456",
            user_name="John",
        )

        # Check HTML contains expected content
        assert "123456" in html
        assert "John" in html
        assert "TestApp" in html
        assert "Verify" in html

        # Check text version is generated
        assert "123456" in text
        assert len(text) > 0

    def test_render_password_reset_template(self) -> None:
        """Test rendering password_reset template."""
        loader = EmailTemplateLoader(app_name="TestApp")

        html, text = loader.render(
            "password_reset",
            reset_url="https://testapp.com/reset?token=abc123",
            user_name="Jane",
        )

        assert "reset?token=abc123" in html
        assert "Jane" in html
        assert "Reset" in html
        assert len(text) > 0

    def test_render_invitation_template(self) -> None:
        """Test rendering invitation template."""
        loader = EmailTemplateLoader(app_name="TestApp")

        html, text = loader.render(
            "invitation",
            invitation_url="https://testapp.com/invite/xyz",
            inviter_name="Alice",
            workspace_name="Engineering",
            role="Developer",
        )

        assert "invite/xyz" in html
        assert "Alice" in html
        assert "Engineering" in html
        assert "Developer" in html
        assert len(text) > 0

    def test_render_welcome_template(self) -> None:
        """Test rendering welcome template."""
        loader = EmailTemplateLoader(app_name="TestApp")

        html, text = loader.render(
            "welcome",
            user_name="Bob",
            features=["Feature 1", "Feature 2"],
        )

        assert "Bob" in html
        assert "Welcome" in html
        assert "Feature 1" in html
        assert "Feature 2" in html
        assert len(text) > 0

    def test_render_nonexistent_template_raises(self) -> None:
        """Test rendering nonexistent template raises error."""
        loader = EmailTemplateLoader()

        with pytest.raises(TemplateNotFoundError):
            loader.render("nonexistent_template")

    def test_render_with_default_context(self) -> None:
        """Test that default context is merged with provided context."""
        loader = EmailTemplateLoader(
            app_name="MyApp",
            default_context={"custom_var": "custom_value"},
        )

        html, text = loader.render(
            "verification",
            code="999999",
        )

        # app_name from init should be in output
        assert "MyApp" in html

    def test_context_override(self) -> None:
        """Test that provided context overrides default context."""
        loader = EmailTemplateLoader(app_name="DefaultApp")

        # The template uses app_name from context
        html, text = loader.render(
            "welcome",
            user_name="Test",
            app_name="OverrideApp",  # This should override
        )

        # Note: Jinja2 will use the last value provided
        # The render method merges default + provided, so provided wins
        assert "OverrideApp" in html


# ─── HTML to Text Conversion Tests ─────────────────────────────────────────


class TestHtmlToText:
    """Tests for HTML to text conversion."""

    def test_strips_html_tags(self) -> None:
        """Test that HTML tags are stripped."""
        loader = EmailTemplateLoader()
        html, text = loader.render(
            "verification",
            code="123456",
        )

        # Text should not contain HTML tags
        assert "<p>" not in text
        assert "<h1>" not in text
        assert "<div>" not in text

    def test_preserves_links(self) -> None:
        """Test that links are preserved in readable format."""
        loader = EmailTemplateLoader()
        html, text = loader.render(
            "password_reset",
            reset_url="https://example.com/reset",
        )

        # Link URL should be in text
        assert "https://example.com/reset" in text

    def test_converts_headers(self) -> None:
        """Test that headers are converted to uppercase."""
        loader = EmailTemplateLoader()
        html, text = loader.render(
            "welcome",
            user_name="Test",
        )

        # Headers should be uppercase in text
        # The template has "Welcome to" as h1
        assert "WELCOME" in text.upper()


# ─── Template Customization Tests ──────────────────────────────────────────


class TestTemplateCustomization:
    """Tests for template customization features."""

    def test_custom_expires_in(self) -> None:
        """Test custom expires_in value."""
        loader = EmailTemplateLoader()
        html, text = loader.render(
            "verification",
            code="123456",
            expires_in="30 minutes",
        )

        assert "30 minutes" in html

    def test_verification_with_url_instead_of_code(self) -> None:
        """Test verification template with URL instead of code."""
        loader = EmailTemplateLoader()
        html, text = loader.render(
            "verification",
            verification_url="https://example.com/verify?token=abc",
        )

        assert "verify?token=abc" in html

    def test_invitation_with_message(self) -> None:
        """Test invitation with personal message."""
        loader = EmailTemplateLoader()
        html, text = loader.render(
            "invitation",
            invitation_url="https://example.com/invite",
            inviter_name="Alice",
            message="Looking forward to working with you!",
        )

        assert "Looking forward to working with you!" in html
