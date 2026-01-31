"""
Email template loader and renderer.

Provides Jinja2-based templating with support for:
- Package-bundled templates
- Custom template directories
- Automatic text version generation from HTML
- Base template inheritance
"""

from __future__ import annotations

import html
import re
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError as e:
    raise ImportError(
        "jinja2 is required for email templates. "
        "Install with: pip install svc-infra[email-templates]"
    ) from e


class TemplateNotFoundError(Exception):
    """Raised when a template cannot be found."""

    pass


class EmailTemplateLoader:
    """
    Email template loader with Jinja2 rendering.

    Provides loading and rendering of email templates with support for:
    - Built-in templates from package resources
    - Custom template directories
    - Automatic plain text generation from HTML
    - Template inheritance with base layouts

    Example:
        >>> loader = EmailTemplateLoader()
        >>>
        >>> # Render verification email
        >>> html, text = loader.render(
        ...     "verification",
        ...     code="123456",
        ...     user_name="John",
        ...     app_name="MyApp",
        ... )
        >>>
        >>> # Render with custom base URL
        >>> html, text = loader.render(
        ...     "password_reset",
        ...     reset_url="https://app.example.com/reset?token=abc123",
        ...     user_name="Jane",
        ... )

    Attributes:
        template_dir: Path to custom templates (None uses built-in)
        default_context: Context variables available in all templates
    """

    def __init__(
        self,
        template_dir: str | Path | None = None,
        *,
        default_context: dict[str, Any] | None = None,
        app_name: str = "Our Service",
        app_url: str = "",
        support_email: str = "",
        unsubscribe_url: str = "",
    ) -> None:
        """
        Initialize template loader.

        Args:
            template_dir: Custom template directory. If None, uses built-in templates.
            default_context: Variables available in all template renders.
            app_name: Application name for branding.
            app_url: Application base URL for links.
            support_email: Support contact email.
            unsubscribe_url: Default unsubscribe URL.
        """
        self.template_dir = Path(template_dir) if template_dir else None
        self.default_context = default_context or {}

        # Branding defaults
        self.default_context.setdefault("app_name", app_name)
        self.default_context.setdefault("app_url", app_url)
        self.default_context.setdefault("support_email", support_email)
        self.default_context.setdefault("unsubscribe_url", unsubscribe_url)

        self._env = self._create_environment()

    def _create_environment(self) -> Environment:
        """Create Jinja2 environment with template loader."""
        if self.template_dir and self.template_dir.exists():
            # Use custom templates with fallback to built-in
            loaders = [
                FileSystemLoader(str(self.template_dir)),
                FileSystemLoader(str(self._get_builtin_path())),
            ]
            from jinja2 import ChoiceLoader

            loader: FileSystemLoader | ChoiceLoader = ChoiceLoader(loaders)
        else:
            # Use built-in templates only
            loader = FileSystemLoader(str(self._get_builtin_path()))

        env = Environment(
            loader=loader,
            autoescape=select_autoescape(["html", "htm", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        env.filters["strip_html"] = self._strip_html
        env.filters["wrap_text"] = self._wrap_text

        return env

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_builtin_path() -> Path:
        """Get path to built-in templates."""
        # Use importlib.resources for package resources
        try:
            # Python 3.9+ - resources.files returns a Traversable
            files = resources.files("svc_infra.email.templates")
            # Use as_file for proper context management with Traversable
            return Path(str(files))
        except (TypeError, AttributeError):
            # Fallback for older Python
            import svc_infra.email.templates as templates_module

            return Path(templates_module.__file__).parent

    def render(
        self,
        template_name: str,
        **context: Any,
    ) -> tuple[str, str]:
        """
        Render an email template.

        Renders both HTML and plain text versions. If a .txt template exists,
        it will be used for the text version. Otherwise, text is auto-generated
        from the HTML.

        Args:
            template_name: Name of the template (without extension)
            **context: Variables to pass to the template

        Returns:
            Tuple of (html_content, text_content)

        Raises:
            TemplateNotFoundError: If template doesn't exist

        Example:
            >>> loader = EmailTemplateLoader()
            >>> html, text = loader.render(
            ...     "verification",
            ...     code="123456",
            ...     user_name="John",
            ... )
        """
        # Merge default context with provided context
        full_context = {**self.default_context, **context}

        # Render HTML version
        html_template_name = f"{template_name}.html"
        try:
            html_template = self._env.get_template(html_template_name)
        except Exception as e:
            raise TemplateNotFoundError(
                f"Template '{template_name}' not found. Looked for: {html_template_name}"
            ) from e

        html_content = html_template.render(**full_context)

        # Try to render text version, or generate from HTML
        text_template_name = f"{template_name}.txt"
        try:
            text_template = self._env.get_template(text_template_name)
            text_content = text_template.render(**full_context)
        except Exception:
            # Auto-generate text from HTML
            text_content = self._html_to_text(html_content)

        return html_content.strip(), text_content.strip()

    def get_available_templates(self) -> list[str]:
        """
        List available template names.

        Returns:
            List of template names (without extensions)
        """
        templates = set()
        for name in self._env.list_templates():
            # Only consider HTML templates, not Python files
            if not name.endswith(".html"):
                continue
            # Strip extension and add base name
            base = name.rsplit(".", 1)[0]
            if not base.startswith("_") and base != "base":
                templates.add(base)
        return sorted(templates)

    def template_exists(self, template_name: str) -> bool:
        """
        Check if a template exists.

        Args:
            template_name: Name of the template (without extension)

        Returns:
            True if template exists
        """
        try:
            self._env.get_template(f"{template_name}.html")
            return True
        except Exception:
            return False

    @staticmethod
    def _strip_html(value: str) -> str:
        """Strip HTML tags from text."""
        # Remove style and script blocks entirely
        value = re.sub(r"<style[^>]*>.*?</style>", "", value, flags=re.DOTALL | re.I)
        value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.DOTALL | re.I)
        # Remove all tags
        value = re.sub(r"<[^>]+>", "", value)
        # Decode HTML entities
        value = html.unescape(value)
        return value

    @staticmethod
    def _wrap_text(value: str, width: int = 70) -> str:
        """Wrap text to specified width."""
        import textwrap

        lines = value.split("\n")
        wrapped = []
        for line in lines:
            if len(line) > width:
                wrapped.extend(textwrap.wrap(line, width=width))
            else:
                wrapped.append(line)
        return "\n".join(wrapped)

    @classmethod
    def _html_to_text(cls, html_content: str) -> str:
        """
        Convert HTML email to plain text.

        Handles common email HTML patterns:
        - Preserves links as [text](url)
        - Converts headers to uppercase
        - Preserves paragraph structure
        - Handles lists and tables
        """
        text = html_content

        # Remove head section
        text = re.sub(r"<head[^>]*>.*?</head>", "", text, flags=re.DOTALL | re.I)

        # Remove style blocks
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.I)

        # Convert <br> to newline
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)

        # Convert block elements to newlines
        text = re.sub(r"</?(p|div|tr|table|section|article)[^>]*>", "\n", text, flags=re.I)

        # Convert headers to uppercase text
        def header_to_text(match: re.Match[str]) -> str:
            content = cls._strip_html(match.group(1))
            return f"\n\n{content.upper()}\n{'=' * len(content)}\n"

        text = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", header_to_text, text, flags=re.DOTALL | re.I)

        # Convert links to markdown-style
        def link_to_text(match: re.Match[str]) -> str:
            href = match.group(1)
            content = cls._strip_html(match.group(2))
            if content and content != href:
                return f"{content} ({href})"
            return href

        text = re.sub(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            link_to_text,
            text,
            flags=re.DOTALL | re.I,
        )

        # Convert list items
        text = re.sub(r"<li[^>]*>", "• ", text, flags=re.I)
        text = re.sub(r"</li>", "\n", text, flags=re.I)

        # Remove remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        text = html.unescape(text)

        # Clean up whitespace
        text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces to single
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Multiple newlines to double
        text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)  # Leading whitespace per line

        return text.strip()
