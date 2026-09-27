"""Password hashing and session tokens.

Passwords are never stored. We store a salted PBKDF2-HMAC-SHA256 hash:

    new accounts:  pbkdf2_sha256$<iterations>$<salt>$<hex digest>   (600,000 iterations, OWASP 2023+)
    seed accounts: pbkdf2_sha256$<salt>$<hex digest>                 (legacy format, 120,000 iterations)
"""

import hashlib
import hmac
import os
import secrets
import time

import jwt

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
LEGACY_ITERATIONS = 120_000

SESSION_COOKIE = "cc_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days

# Signs session cookies. Set AUTH_SECRET_KEY in .env to keep sessions across restarts;
# otherwise a random key is generated each time the server starts.
SECRET_KEY = os.getenv("AUTH_SECRET_KEY") or secrets.token_urlsafe(48)


def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"{ALGORITHM}${ITERATIONS}${salt}${_pbkdf2(password, salt, ITERATIONS)}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4 and parts[0] == ALGORITHM and parts[1].isdigit():
        _, iterations, salt, digest = parts
        iterations = int(iterations)
    elif len(parts) == 3 and parts[0] == ALGORITHM:
        _, salt, digest = parts
        iterations = LEGACY_ITERATIONS
    else:
        return False
    # Constant-time comparison so response timing doesn't leak how many characters matched.
    return hmac.compare_digest(_pbkdf2(password, salt, iterations), digest)


# Verified against when the email doesn't exist, so "unknown email" and "wrong password"
# take the same time and attackers can't discover which emails have accounts.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def create_session_token(user_id: int) -> str:
    now = int(time.time())
    return jwt.encode({"sub": str(user_id), "iat": now, "exp": now + SESSION_TTL_SECONDS}, SECRET_KEY, algorithm="HS256")


def read_session_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


class LoginRateLimiter:
    """Blocks brute-force guessing: max 5 failed logins per email or IP per 15 minutes."""

    def __init__(self, max_failures: int = 5, window_seconds: int = 15 * 60):
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: dict[str, list[float]] = {}

    def _recent(self, key: str) -> list[float]:
        cutoff = time.time() - self.window
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        self._failures[key] = recent
        return recent

    def is_blocked(self, *keys: str) -> bool:
        return any(len(self._recent(k)) >= self.max_failures for k in keys)

    def record_failure(self, *keys: str) -> None:
        for k in keys:
            self._recent(k).append(time.time())

    def reset(self, *keys: str) -> None:
        for k in keys:
            self._failures.pop(k, None)
