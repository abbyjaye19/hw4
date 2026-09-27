"""Create-account / login / logout / current-user endpoints."""

import sqlite3

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field, field_validator

from db import get_db
from security import (
    DUMMY_HASH,
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    LoginRateLimiter,
    create_session_token,
    hash_password,
    read_session_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
rate_limiter = LoginRateLimiter()


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PublicUser(BaseModel):
    """What the browser (and later the agent) may see. Never includes password_hash."""

    id: int
    first_name: str
    last_name: str
    name: str
    email: str
    created_at: str


def public_user(row: sqlite3.Row) -> PublicUser:
    first = row["first_name"] or row["name"].split(" ")[0]
    last = row["last_name"] or " ".join(row["name"].split(" ")[1:])
    return PublicUser(
        id=row["id"], first_name=first, last_name=last, name=row["name"], email=row["email"], created_at=row["created_at"]
    )


def set_session_cookie(response: Response, user_id: int) -> None:
    # HttpOnly: page JavaScript (and any injected script) cannot read the token.
    # SameSite=Lax: other sites cannot make logged-in requests on the shopper's behalf.
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(user_id),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,  # set True when served over HTTPS
        path="/",
    )


def get_current_user(token: str | None) -> PublicUser | None:
    user_id = read_session_token(token) if token else None
    if user_id is None:
        return None
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return public_user(row) if row else None


@router.post("/register", status_code=201)
def register(body: RegisterRequest, response: Response) -> PublicUser:
    email = body.email.lower()
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(status_code=409, detail="An account with that email already exists.")
        cur = conn.execute(
            "INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
            (f"{body.first_name} {body.last_name}", body.first_name, body.last_name, email, hash_password(body.password)),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    set_session_cookie(response, row["id"])
    return public_user(row)


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response) -> PublicUser:
    email = body.email.lower()
    keys = (f"email:{email}", f"ip:{request.client.host if request.client else 'unknown'}")
    if rate_limiter.is_blocked(*keys):
        raise HTTPException(status_code=429, detail="Too many failed attempts. Please wait 15 minutes and try again.")

    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
    ok = verify_password(body.password, row["password_hash"] if row else DUMMY_HASH) and row is not None
    if not ok:
        rate_limiter.record_failure(*keys)
        # Same message whether the email or the password was wrong.
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    rate_limiter.reset(*keys)
    set_session_cookie(response, row["id"])
    return public_user(row)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me")
def me(cc_session: str | None = Cookie(default=None)) -> PublicUser | None:
    """The logged-in shopper, or null for guests (a normal state, so not an error)."""
    return get_current_user(cc_session)
