"""URL content loader.

Load content from URLs with automatic HTML text extraction.
"""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from svc_infra.http import new_async_httpx_client

from .base import BaseLoader, ErrorStrategy
from .models import LoadedContent

logger = logging.getLogger(__name__)

_DEFAULT_PUBLIC_FETCH_MAX_BYTES = 1_048_576
_DEFAULT_PUBLIC_FETCH_MAX_REDIRECTS = 5
_DEFAULT_PUBLIC_FETCH_USER_AGENT = "svc-infra-url-loader/1.0"


class PublicURLPolicyError(RuntimeError):
    """Raised when a public URL fetch violates network access policy."""


class URLContentTooLargeError(RuntimeError):
    """Raised when a fetched URL response exceeds the configured byte cap."""


def _validate_http_url(url: str) -> None:
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL: {url!r}. URLs must start with http:// or https://")


def _is_public_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_global


def _validate_public_hostname(hostname: str | None) -> None:
    if not hostname:
        raise PublicURLPolicyError("Public URL fetch requires a resolvable hostname.")

    try:
        infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise PublicURLPolicyError(
            f"Could not resolve host for public URL fetch: {hostname}"
        ) from exc

    addresses: set[str] = set()
    for info in infos:
        if not info[4]:
            continue
        address = info[4][0]
        if isinstance(address, str):
            addresses.add(address)

    if not addresses:
        raise PublicURLPolicyError(f"Could not resolve host for public URL fetch: {hostname}")

    non_public = sorted(address for address in addresses if not _is_public_ip(address))
    if non_public:
        raise PublicURLPolicyError(
            f"URL host resolves to non-public IP addresses and is not allowed: {hostname}"
        )


async def _read_response_bytes(response: httpx.Response, max_bytes: int | None) -> bytes:
    if max_bytes is not None:
        content_length = response.headers.get("content-length", "").strip()
        if content_length:
            try:
                if int(content_length) > max_bytes:
                    raise URLContentTooLargeError(
                        "URL response exceeds the configured size limit before download completed."
                    )
            except ValueError:
                pass

    chunks: list[bytes] = []
    total_bytes = 0
    async for chunk in response.aiter_bytes():
        total_bytes += len(chunk)
        if max_bytes is not None and total_bytes > max_bytes:
            raise URLContentTooLargeError("URL response exceeds the configured size limit.")
        chunks.append(chunk)
    return b"".join(chunks)


def _decode_response_text(response: httpx.Response, raw_content: bytes) -> str:
    encoding = response.encoding or "utf-8"
    return raw_content.decode(encoding, errors="replace")


def _build_loaded_content(
    *,
    requested_url: str,
    final_url: str,
    response: httpx.Response,
    raw_content: bytes,
    extract_text: bool,
    extra_metadata: dict[str, Any] | None = None,
    redirect_count: int = 0,
) -> LoadedContent:
    content_type = response.headers.get("content-type", "")
    raw_text = _decode_response_text(response, raw_content)
    if extract_text and "text/html" in content_type:
        content = URLLoader._extract_text_from_html(raw_text)
    else:
        content = raw_text

    mime_type = content_type.split(";")[0].strip() if content_type else None
    return LoadedContent(
        content=content,
        source=requested_url,
        content_type=mime_type,
        metadata={
            "loader": "url",
            "url": requested_url,
            "status_code": response.status_code,
            "final_url": final_url,
            "redirect_count": redirect_count,
            **(extra_metadata or {}),
        },
    )


async def fetch_public_url(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    extract_text: bool = True,
    timeout: float = 30.0,
    extra_metadata: dict[str, Any] | None = None,
    max_bytes: int = _DEFAULT_PUBLIC_FETCH_MAX_BYTES,
    max_redirects: int = _DEFAULT_PUBLIC_FETCH_MAX_REDIRECTS,
    user_agent: str = _DEFAULT_PUBLIC_FETCH_USER_AGENT,
) -> LoadedContent:
    """Fetch a public HTTP(S) URL with SSRF protections and byte caps."""
    _validate_http_url(url)

    request_headers = dict(headers or {})
    request_headers.setdefault("User-Agent", user_agent)

    current_url = url
    redirect_count = 0

    async with new_async_httpx_client(
        timeout_seconds=timeout,
        follow_redirects=False,
    ) as client:
        while True:
            parsed = urlparse(current_url)
            _validate_http_url(current_url)
            _validate_public_hostname(parsed.hostname)

            async with client.stream("GET", current_url, headers=request_headers) as response:
                if 300 <= response.status_code < 400:
                    location = response.headers.get("location", "").strip()
                    if not location:
                        raise PublicURLPolicyError(
                            "Redirect response did not include a location header."
                        )
                    if redirect_count >= max_redirects:
                        raise PublicURLPolicyError("Too many redirects while fetching public URL.")
                    current_url = urljoin(current_url, location)
                    redirect_count += 1
                    continue

                response.raise_for_status()
                raw_content = await _read_response_bytes(response, max_bytes=max_bytes)
                return _build_loaded_content(
                    requested_url=url,
                    final_url=str(response.url),
                    response=response,
                    raw_content=raw_content,
                    extract_text=extract_text,
                    extra_metadata=extra_metadata,
                    redirect_count=redirect_count,
                )


class URLLoader(BaseLoader):
    """Load content from one or more URLs.

    Fetches content from URLs and optionally extracts readable text from HTML.
    Supports redirects, custom headers, and batch loading.

    Args:
        urls: Single URL or list of URLs to load.
        headers: Optional HTTP headers to send with requests.
        extract_text: If True (default), extract readable text from HTML pages.
            Raw HTML is returned if False or if content is not HTML.
        follow_redirects: Follow HTTP redirects (default: True).
        timeout: Request timeout in seconds (default: 30).
        extra_metadata: Additional metadata to attach to all loaded content.
        public_only: If True, only allow publicly routable HTTP(S) targets and
            validate every redirect hop.
        max_bytes: Optional response byte limit.
        max_redirects: Maximum redirect hops when public_only=True.
        on_error: How to handle errors ("skip" or "raise"). Default: "skip"

    Example:
        >>> # Load single URL
        >>> loader = URLLoader("https://example.com/docs/guide.md")
        >>> contents = await loader.load()
        >>> print(contents[0].content[:100])
        >>>
        >>> # Load multiple URLs
        >>> loader = URLLoader([
        ...     "https://example.com/page1",
        ...     "https://example.com/page2",
        ... ])
        >>> contents = await loader.load()
        >>>
        >>> # Disable HTML text extraction
        >>> loader = URLLoader("https://example.com", extract_text=False)
        >>> contents = await loader.load()  # Returns raw HTML
        >>>
        >>> # With custom headers (e.g., for APIs)
        >>> loader = URLLoader(
        ...     "https://api.example.com/docs",
        ...     headers={"Authorization": "Bearer token123"},
        ... )
        >>> contents = await loader.load()

    Note:
        - HTML text extraction removes scripts, styles, nav, footer, etc.
        - If BeautifulSoup is not installed, falls back to basic regex extraction
        - Content type is detected from HTTP headers
    """

    def __init__(
        self,
        urls: str | list[str],
        headers: dict[str, str] | None = None,
        extract_text: bool = True,
        follow_redirects: bool = True,
        timeout: float = 30.0,
        extra_metadata: dict[str, Any] | None = None,
        public_only: bool = False,
        max_bytes: int | None = None,
        max_redirects: int = _DEFAULT_PUBLIC_FETCH_MAX_REDIRECTS,
        on_error: ErrorStrategy = "skip",
    ) -> None:
        """Initialize the URL loader.

        Args:
            urls: Single URL or list of URLs
            headers: HTTP headers to send
            extract_text: Extract text from HTML (default: True)
            follow_redirects: Follow redirects (default: True)
            timeout: Request timeout in seconds
            extra_metadata: Additional metadata for all content
            on_error: Error handling strategy
        """
        super().__init__(on_error=on_error)

        # Normalize urls to list
        self.urls = [urls] if isinstance(urls, str) else list(urls)
        self.headers = headers or {}
        self.extract_text = extract_text
        self.follow_redirects = follow_redirects
        self.timeout = timeout
        self.extra_metadata = extra_metadata or {}
        self.public_only = public_only
        self.max_bytes = max_bytes
        self.max_redirects = max_redirects

        # Validate URLs
        for url in self.urls:
            _validate_http_url(url)

    async def load(self) -> list[LoadedContent]:
        """Load content from all URLs.

        Returns:
            List of LoadedContent objects for each successfully loaded URL.

        Raises:
            httpx.HTTPError: If request fails and on_error="raise".
        """
        contents: list[LoadedContent] = []

        if self.public_only:
            for url in self.urls:
                try:
                    contents.append(
                        await fetch_public_url(
                            url,
                            headers=self.headers,
                            extract_text=self.extract_text,
                            timeout=self.timeout,
                            extra_metadata=self.extra_metadata,
                            max_bytes=self.max_bytes or _DEFAULT_PUBLIC_FETCH_MAX_BYTES,
                            max_redirects=self.max_redirects,
                        )
                    )
                except (PublicURLPolicyError, URLContentTooLargeError, httpx.HTTPError) as e:
                    msg = f"Request failed for {url}: {e}"
                    if self.on_error == "raise":
                        raise RuntimeError(msg) from e
                    logger.warning(msg)
            return contents

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
        ) as client:
            for url in self.urls:
                try:
                    logger.debug(f"Fetching: {url}")
                    resp = await client.get(url, headers=self.headers)
                    resp.raise_for_status()

                    content_type = resp.headers.get("content-type", "")
                    raw_content = resp.text

                    # Extract text from HTML if requested
                    if self.extract_text and "text/html" in content_type:
                        content = self._extract_text_from_html(raw_content)
                    else:
                        content = raw_content

                    # Parse content type (remove charset etc.)
                    mime_type = content_type.split(";")[0].strip() if content_type else None

                    loaded = LoadedContent(
                        content=content,
                        source=url,
                        content_type=mime_type,
                        metadata={
                            "loader": "url",
                            "url": url,
                            "status_code": resp.status_code,
                            "final_url": str(resp.url),  # After redirects
                            **self.extra_metadata,
                        },
                    )
                    contents.append(loaded)
                    logger.debug(f"Loaded: {url} ({len(content)} chars)")

                except httpx.HTTPStatusError as e:
                    msg = f"HTTP {e.response.status_code} for {url}"
                    if self.on_error == "raise":
                        raise RuntimeError(msg) from e
                    logger.warning(msg)

                except httpx.RequestError as e:
                    msg = f"Request failed for {url}: {e}"
                    if self.on_error == "raise":
                        raise RuntimeError(msg) from e
                    logger.warning(msg)

        return contents

    @staticmethod
    def _extract_text_from_html(html: str) -> str:
        """Extract readable text from HTML content.

        Tries to use BeautifulSoup if available, falls back to regex.

        Args:
            html: Raw HTML content

        Returns:
            Extracted text with scripts, styles, and navigation removed.
        """
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()

            # Get text with newlines preserved
            text = soup.get_text(separator="\n", strip=True)

            # Clean up excessive whitespace
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text.strip()

        except ImportError:
            # Fallback: basic regex-based extraction
            logger.debug("BeautifulSoup not installed, using regex fallback")

            # Remove script and style blocks
            text = re.sub(
                r"<script[^>]*>.*?</script>",
                "",
                html,
                flags=re.DOTALL | re.IGNORECASE,
            )
            text = re.sub(
                r"<style[^>]*>.*?</style>",
                "",
                text,
                flags=re.DOTALL | re.IGNORECASE,
            )

            # Remove all HTML tags
            text = re.sub(r"<[^>]+>", " ", text)

            # Decode common HTML entities
            text = text.replace("&nbsp;", " ")
            text = text.replace("&amp;", "&")
            text = text.replace("&lt;", "<")
            text = text.replace("&gt;", ">")
            text = text.replace("&quot;", '"')
            text = text.replace("&#39;", "'")

            # Clean up whitespace
            text = " ".join(text.split())
            return text.strip()

    def __repr__(self) -> str:
        """Return string representation."""
        if len(self.urls) == 1:
            return f"URLLoader({self.urls[0]!r})"
        return f"URLLoader([{len(self.urls)} URLs])"
