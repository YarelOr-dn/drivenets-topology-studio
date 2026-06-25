"""Username / email validation shared by seed + migration + auth.

Single source of truth for "what is a valid topology username" and
"how do we derive a username from a verified company email". Pulled out
of ``schemas.py`` so the seed tool and migration scripts (which run
outside the FastAPI request lifecycle) can reuse the *exact* same rules
without importing pydantic.

The username regex below is kept identical to ``LoginRequest.username``
in ``api/schemas.py``. If you change one, change both.
"""

from __future__ import annotations

import re
from typing import Optional


COMPANY_DOMAIN = "drivenets.com"
COMPANY_TYPO_DOMAINS = {"drivents.com"}

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.\-]+$")
USERNAME_MIN_LEN = 2
USERNAME_MAX_LEN = 64


class InvalidIdentityError(ValueError):
    """Raised when a username or email cannot be used by the topology app."""


def normalise_email(email: Optional[str]) -> str:
    """Lowercase + strip an email; return ``""`` for ``None`` / blank."""
    if not email:
        return ""
    return email.strip().lower()


def is_company_email(email: Optional[str]) -> bool:
    """True iff ``email`` is a non-typo ``@drivenets.com`` address.

    The user explicitly called out ``@drivents.com`` as a typo so we
    refuse it here -- otherwise a fat-fingered Confluence record could
    leak into our user DB.
    """
    e = normalise_email(email)
    if "@" not in e:
        return False
    domain = e.rsplit("@", 1)[-1]
    if domain in COMPANY_TYPO_DOMAINS:
        return False
    return domain == COMPANY_DOMAIN


def validate_username(username: str, *, allow_short: bool = False) -> str:
    """Return ``username`` if valid, else raise :class:`InvalidIdentityError`.

    ``allow_short`` widens the lower bound from 2 to 1 char to match the
    legacy ``LoginRequest`` (length >= 1). Registration / seed always
    requires at least 2 chars.
    """
    if not isinstance(username, str):
        raise InvalidIdentityError("username must be a string")
    u = username.strip()
    min_len = 1 if allow_short else USERNAME_MIN_LEN
    if not (min_len <= len(u) <= USERNAME_MAX_LEN):
        raise InvalidIdentityError(
            f"username length must be {min_len}..{USERNAME_MAX_LEN} (got {len(u)})"
        )
    if not USERNAME_REGEX.match(u):
        raise InvalidIdentityError(
            f"username {u!r} contains characters outside [a-zA-Z0-9_.-]"
        )
    return u


def derive_username_from_email(email: str) -> str:
    """Strip the local part out of a company email and validate it.

    The local part is lowercased and must satisfy :func:`validate_username`.
    We deliberately do NOT mutate the local part (no character substitution,
    no truncation): if the original email cannot map cleanly to a topology
    username we want to surface that to the operator rather than silently
    inventing a different identity.
    """
    if not is_company_email(email):
        raise InvalidIdentityError(
            f"email {email!r} is not a valid @{COMPANY_DOMAIN} address"
        )
    local = email.strip().lower().split("@", 1)[0]
    return validate_username(local)


def safe_derive_username_from_email(email: str) -> Optional[str]:
    """Non-raising variant of :func:`derive_username_from_email`."""
    try:
        return derive_username_from_email(email)
    except InvalidIdentityError:
        return None
