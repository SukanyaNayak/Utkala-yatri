"""
UtkalaYatri — authentication backend (FastAPI + MongoDB)
========================================================
User accounts stored in a MongoDB collection, passwords hashed with
bcrypt, sessions issued as JWT bearer tokens. Drop-in replacement for
the SQLite `auth_backend.py`: same `auth_router`, same `init_auth_db`,
same endpoints, same error keys — the frontend never notices the swap.

WHY MONGO (instead of the SQLite file)
  The SQLite version kept accounts in `yatri.db` on Render's EPHEMERAL
  disk — every redeploy wiped all users. MongoDB Atlas stores accounts
  outside the container, so users survive redeploys and restarts.

WHERE TO PUT IT
  backend/auth_backend.py        ← this file (rename it to auth_backend.py!)
  It is picked up automatically: main-complete.py already does
      from auth_backend import auth_router, init_auth_db
      init_auth_db()
      app.include_router(auth_router)
  inside try/except — if MongoDB is unreachable, auth quietly disables
  itself and every data endpoint (places, festivals, hotels…) still works.

ENVIRONMENT VARIABLES (Render → Environment → Add Environment Variable)
  MONGODB_URI         required  e.g. mongodb+srv://user:pass@cluster/…
                      (Atlas: Database → Connect → Drivers → the srv string;
                       URL-encode the password if it has special characters)
  MONGODB_DB          optional  database name, default "utkalayatri"
  JWT_SECRET          optional  fixed signing secret; if unset, one is
                      generated ONCE and stored inside MongoDB itself, so
                      sessions survive redeploys either way
  MONGODB_TIMEOUT_MS  optional  server-selection timeout, default 8000

Atlas one-time setup: Network Access → ADD IP ADDRESS → "Allow access from
anywhere" (0.0.0.0/0) — Render's outbound IPs are not allow-listed by
default and the backend cannot reach the cluster without this.

ENDPOINTS (unchanged from the SQLite version)
  POST /api/auth/signup  {name, email, password}  → {token, user}
  POST /api/auth/login   {email, password}        → {token, user}
  GET  /api/auth/me      (Authorization: Bearer)  → {user}

ERROR CONTRACT (the value of "error"/"detail" is always an i18n key):
  auth_err_name, auth_err_email, auth_err_password,
  auth_err_exists, auth_err_invalid, auth_err_generic
The Login page translates them directly with t(error), falling back to
auth_err_generic — so errors display in English / हिन्दी / ଓଡ଼ିଆ automatically.
"""

import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel

# ── config ────────────────────────────────────────────────────────────────
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "Utkalayatri")
SERVER_TIMEOUT_MS = int(os.environ.get("MONGODB_TIMEOUT_MS", "8000"))
TOKEN_DAYS = 7

_client: MongoClient | None = None


def _db():
    """Lazily connected handle — importing this module never blocks."""
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=SERVER_TIMEOUT_MS)
    return _client[MONGODB_DB]


def users_col():
    return _db()["users"]


# The JWT secret lives in JWT_SECRET if set, otherwise it is generated once
# and persisted INSIDE MongoDB (a config doc) so existing sessions keep
# working after Render redeploys the container. If MongoDB is unreachable at
# startup we fall back to an in-memory secret — auth still runs until restart.
def _load_secret() -> str:
    env = os.environ.get("JWT_SECRET")
    if env:
        return env
    try:
        col = _db()["config"]
        doc = col.find_one({"key": "jwt_secret"})
        if doc:
            return doc["value"]
        secret = secrets.token_hex(32)
        col.update_one(
            {"key": "jwt_secret"}, {"$setOnInsert": {"value": secret}}, upsert=True
        )
        return col.find_one({"key": "jwt_secret"})["value"]
    except Exception:
        return secrets.token_hex(32)


JWT_SECRET = _load_secret()


# ── database ──────────────────────────────────────────────────────────────
def init_auth_db() -> None:
    """Creates the unique email index. Safe to call on every startup."""
    users_col().create_index("email", unique=True)


def _public_user(doc: dict) -> dict:
    created = doc.get("created_at")
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "created_at": created.isoformat() if hasattr(created, "isoformat") else "",
    }


# ── schemas ───────────────────────────────────────────────────────────────
class SignupBody(BaseModel):
    name: str
    email: str
    password: str


class LoginBody(BaseModel):
    email: str
    password: str


# ── helpers ───────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _hash_password(password: str) -> str:
    # bcrypt only uses the first 72 bytes; long passphrases are truncated.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode()


def _make_token(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _issue(doc: dict) -> dict:
    return {"token": _make_token(doc["_id"]), "user": _public_user(doc)}


bearer = HTTPBearer(auto_error=False)


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    """Dependency: resolve the Bearer token to a users doc (401 otherwise)."""
    if creds is None:
        raise HTTPException(401, detail="auth_err_invalid")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(401, detail="auth_err_invalid")
    try:
        doc = users_col().find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise HTTPException(401, detail="auth_err_invalid")
    if doc is None:
        raise HTTPException(401, detail="auth_err_invalid")
    return doc


# ── routes ────────────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


@auth_router.post("/signup")
def signup(body: SignupBody) -> dict:
    name = body.name.strip()
    email = body.email.strip().lower()

    if not name or len(name) > 80:
        raise HTTPException(400, detail="auth_err_name")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, detail="auth_err_email")
    if len(body.password) < 8:
        raise HTTPException(400, detail="auth_err_password")

    pw_hash = _hash_password(body.password)
    try:
        result = users_col().insert_one(
            {
                "name": name,
                "email": email,
                "password_hash": pw_hash,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except DuplicateKeyError:
        raise HTTPException(409, detail="auth_err_exists")

    doc = users_col().find_one({"_id": result.inserted_id})
    return _issue(doc)


@auth_router.post("/login")
def login(body: LoginBody) -> dict:
    email = body.email.strip().lower()
    doc = users_col().find_one({"email": email})
    # Same error for unknown email and wrong password — never reveal which.
    if doc is None or not bcrypt.checkpw(
        body.password.encode("utf-8")[:72], doc["password_hash"].encode()
    ):
        raise HTTPException(401, detail="auth_err_invalid")
    return _issue(doc)


@auth_router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    return {"user": _public_user(user)}
