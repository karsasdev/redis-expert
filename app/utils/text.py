import re
from typing import List


def normalize(s: str) -> str:
    """Lowercase and strip whitespace."""
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokens(s: str) -> List[str]:
    """Extract alphanumeric tokens from a normalized string."""
    s = normalize(s)
    return re.findall(r"[a-z0-9_\-]+", s)
