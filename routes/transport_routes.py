"""Request bodies carried in headers.

The endpoint's [reverse_proxy] (1.1.0) forwards request *headers* but never the
request *body*: it announces content-length to the origin and then sends nothing,
so every POST/PUT hangs until it times out. GET, query strings and arbitrary
headers pass through intact. So the panel sends its JSON payload in x-tt-b*
headers and this middleware rebuilds the body before routing, which makes the
panel work identically with or without a proxy in front.

Payloads too large for one header set are uploaded in pieces through /api/_tx
(itself carried inline) and referenced by id.
"""

import base64
import binascii
import secrets
import threading
import time

from fastapi import HTTPException, Request

from auth import require_auth
from routes import app

# One header set. Chunks are ~1.5 KB each; browsers and the endpoint's HPACK
# both cope well past this, and the panel's real payloads are ~2 KB.
MAX_INLINE_CHUNKS = 16
MAX_INLINE_BYTES = 96 * 1024

# Multi-request uploads (large CSV imports, long rule sets).
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_UPLOAD_PARTS = 512
MAX_UPLOADS = 4
UPLOAD_TTL = 120

_lock = threading.Lock()
_uploads: dict[str, dict] = {}


def _b64u_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _prune_locked(now: float) -> None:
    for key in [k for k, v in _uploads.items() if now - v["ts"] > UPLOAD_TTL]:
        _uploads.pop(key, None)


def _take_upload(upload_id: str) -> bytes:
    now = time.time()
    with _lock:
        _prune_locked(now)
        entry = _uploads.pop(upload_id, None)
    if entry is None:
        raise ValueError("upload expired or unknown")
    if len(entry["parts"]) != entry["total"]:
        raise ValueError("upload incomplete")
    return b"".join(entry["parts"][i] for i in range(entry["total"]))


def _assemble(headers: list[tuple[bytes, bytes]]) -> bytes:
    """Rebuild the request body from x-tt-b* / x-tt-u headers."""
    found = {}
    upload_id = None
    count = None
    for key, value in headers:
        if key == b"x-tt-u":
            upload_id = value.decode("latin1")
        elif key == b"x-tt-b":
            count = value.decode("latin1")
        elif key.startswith(b"x-tt-b"):
            found[key[6:].decode("latin1")] = value

    if upload_id is not None:
        return _take_upload(upload_id)

    try:
        n = int(count)
    except (TypeError, ValueError):
        raise ValueError("bad chunk count")
    if not 0 < n <= MAX_INLINE_CHUNKS:
        raise ValueError("bad chunk count")

    chunks = []
    total = 0
    for i in range(n):
        piece = found.get(str(i))
        if piece is None:
            raise ValueError("missing chunk %d" % i)
        total += len(piece)
        if total > MAX_INLINE_BYTES:
            raise ValueError("payload too large")
        chunks.append(piece.decode("latin1"))
    try:
        return _b64u_decode("".join(chunks))
    except (binascii.Error, ValueError):
        raise ValueError("bad payload encoding")


async def _reject(send, detail: str) -> None:
    body = b'{"detail":"%s"}' % detail.encode("utf-8").replace(b'"', b"'")
    await send({
        "type": "http.response.start",
        "status": 400,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body})


class HeaderBodyTransport:
    """Turns x-tt-b*/x-tt-u headers back into a normal request body."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = scope.get("headers") or []
        if not any(k == b"x-tt-u" or k.startswith(b"x-tt-b") for k, _ in headers):
            return await self.app(scope, receive, send)

        try:
            payload = _assemble(headers)
        except ValueError as exc:
            return await _reject(send, str(exc))

        clean = [
            (k, v) for k, v in headers
            if k != b"x-tt-u" and not k.startswith(b"x-tt-b") and k != b"content-length"
        ]
        if not any(k == b"content-type" for k, _ in clean):
            clean.append((b"content-type", b"application/json"))
        clean.append((b"content-length", str(len(payload)).encode()))
        scope = dict(scope, headers=clean)

        sent = False

        async def _receive():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": payload, "more_body": False}
            # Drain the real (empty) body, then relay disconnects.
            message = await receive()
            while message["type"] == "http.request":
                message = await receive()
            return message

        return await self.app(scope, _receive, send)


app.add_middleware(HeaderBodyTransport)


@app.post("/api/_tx")
async def upload_chunk(request: Request):
    """Buffer one piece of an oversized payload; see the module docstring."""
    await require_auth(request)
    body = await request.json()
    upload_id = body.get("id")
    seq = body.get("seq")
    total = body.get("total")
    data = body.get("data")

    if not isinstance(upload_id, str) or not 8 <= len(upload_id) <= 64:
        raise HTTPException(400, "Bad upload id")
    if not isinstance(total, int) or not 0 < total <= MAX_UPLOAD_PARTS:
        raise HTTPException(400, "Bad part count")
    if not isinstance(seq, int) or not 0 <= seq < total:
        raise HTTPException(400, "Bad part index")
    if not isinstance(data, str):
        raise HTTPException(400, "Bad part")

    piece = data.encode("utf-8")
    now = time.time()
    with _lock:
        _prune_locked(now)
        entry = _uploads.get(upload_id)
        if entry is None:
            if len(_uploads) >= MAX_UPLOADS:
                raise HTTPException(429, "Too many uploads in flight")
            entry = {"parts": {}, "total": total, "ts": now, "size": 0}
            _uploads[upload_id] = entry
        if entry["total"] != total:
            raise HTTPException(400, "Part count mismatch")
        if entry["size"] + len(piece) > MAX_UPLOAD_BYTES:
            _uploads.pop(upload_id, None)
            raise HTTPException(413, "Payload too large")
        if seq not in entry["parts"]:
            entry["size"] += len(piece)
        entry["parts"][seq] = piece
        entry["ts"] = now
        received = len(entry["parts"])

    return {"ok": True, "received": received, "total": total}


@app.get("/api/_tx/new")
async def new_upload_id(request: Request):
    await require_auth(request)
    return {"id": secrets.token_urlsafe(12)}
