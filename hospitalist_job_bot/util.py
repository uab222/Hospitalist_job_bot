"""Small shared helpers."""

from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def extract_email(text: str) -> str:
    """Best-effort extraction of an application email from free text (e.g. a
    posting's description sometimes says 'email your CV to jobs@hospital.org').
    Returns '' if none found."""
    if not text:
        return ""
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""
