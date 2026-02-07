import base64
import hashlib
import io
import os
from datetime import UTC

import pyotp
import segno


def _qr_svg_from_uri(uri: str) -> str:
    """Generate an SVG QR code from an otpauth:// URI."""
    import re

    qr = segno.make(uri)
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=5, border=2, xmldecl=False, svgns=False)
    svg = buf.getvalue().decode("utf-8")
    # Add viewBox so the SVG scales with CSS instead of using fixed dimensions
    m = re.search(r'width="(\d+)"\s+height="(\d+)"', svg)
    if m:
        w, h = m.group(1), m.group(2)
        svg = svg.replace(
            f'width="{w}" height="{h}"',
            f'viewBox="0 0 {w} {h}"',
        )
    return svg


def _random_base32() -> str:
    return pyotp.random_base32(length=32)


def _gen_recovery_codes(n: int, length: int) -> list[str]:
    out = []
    for _ in range(n):
        raw = base64.urlsafe_b64encode(os.urandom(24)).decode().rstrip("=")
        out.append(raw[:length])
    return out


def _gen_numeric_code(n: int = 6) -> str:
    import random

    code = "".join(str(random.randrange(10)) for _ in range(n))
    return code


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _now_utc_ts() -> int:
    from datetime import datetime

    return int(datetime.now(UTC).timestamp())
