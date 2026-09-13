import asyncio
import csv
import io
from datetime import datetime

from fastapi import HTTPException, Request
from fastapi.responses import Response

from auth import load_panel_db, update_panel_db, require_auth
from services import (
    parse_credentials, update_credentials, export_client_config,
    generate_password, schedule_reload, EXPORT_FORMATS, USERNAME_RE,
)
from routes import app

MAX_IMPORT_ROWS = 5000
MAX_PASSWORD_LEN = 128


def _valid_username(name: str) -> bool:
    return bool(USERNAME_RE.match(name or ""))


def _csv_safe(value):
    """Neutralise spreadsheet formula injection on export."""
    s = "" if value is None else str(value)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


def _clean_created(value):
    v = (value or "").strip()
    if v:
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            pass
    return datetime.now().isoformat(timespec="seconds")


@app.get("/api/users")
async def list_users(request: Request):
    await require_auth(request)
    clients = await asyncio.to_thread(parse_credentials)
    return {"users": [{"username": c["username"], "password": c.get("password", ""), "enabled": c.get("enabled", True), "created_at": c.get("created_at", "")} for c in clients]}


@app.post("/api/users")
async def add_user(request: Request):
    await require_auth(request)
    body = await request.json()
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", "")).strip() or generate_password()
    if not username:
        raise HTTPException(400, "Username required")
    if not _valid_username(username):
        raise HTTPException(400, "Username must be 1-64 chars: letters, digits, hyphens, underscores")
    if len(password) > MAX_PASSWORD_LEN:
        raise HTTPException(400, "Password too long")

    def _mutate(clients):
        if any(c["username"] == username for c in clients):
            raise HTTPException(400, "User exists")
        clients.append({
            "username": username, "password": password,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "enabled": True,
        })

    await asyncio.to_thread(update_credentials, _mutate)
    schedule_reload("user_add:" + username)
    return {"ok": True, "username": username, "password": password}


@app.put("/api/users/{username}")
async def update_user(username: str, request: Request):
    await require_auth(request)
    body = await request.json()
    pw = str(body.get("password", "")).strip()
    if not pw:
        raise HTTPException(400, "Password required")
    if len(pw) > MAX_PASSWORD_LEN:
        raise HTTPException(400, "Password too long")

    def _mutate(clients):
        for c in clients:
            if c["username"] == username:
                c["password"] = pw
                return True
        return False

    if not await asyncio.to_thread(update_credentials, _mutate):
        raise HTTPException(404, "Not found")
    schedule_reload("password_change:" + username)
    return {"ok": True}


@app.delete("/api/users/{username}")
async def delete_user(username: str, request: Request):
    await require_auth(request)

    def _mutate(clients):
        before = len(clients)
        clients[:] = [c for c in clients if c["username"] != username]
        return len(clients) != before

    if not await asyncio.to_thread(update_credentials, _mutate):
        raise HTTPException(404, "Not found")
    schedule_reload("user_delete:" + username)
    return {"ok": True}


@app.put("/api/users/{username}/toggle")
async def toggle_user(username: str, request: Request):
    await require_auth(request)

    def _mutate(clients):
        for c in clients:
            if c["username"] == username:
                c["enabled"] = not c.get("enabled", True)
                return c["enabled"]
        return None

    enabled = await asyncio.to_thread(update_credentials, _mutate)
    if enabled is None:
        raise HTTPException(404, "Not found")
    schedule_reload(("user_enable" if enabled else "user_disable") + ":" + username)
    return {"ok": True, "enabled": enabled}


@app.get("/api/users/export")
async def export_users(request: Request):
    await require_auth(request)
    clients = await asyncio.to_thread(parse_credentials)
    db = await asyncio.to_thread(load_panel_db)
    notes = db.get("user_notes", {})
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["username", "password", "enabled", "created_at", "note"])
    for c in clients:
        writer.writerow([
            _csv_safe(c["username"]), _csv_safe(c.get("password", "")),
            c.get("enabled", True), _csv_safe(c.get("created_at", "")),
            _csv_safe(notes.get(c["username"], "")),
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )


@app.get("/api/users/{username}/config")
async def get_user_config(username: str, request: Request, fmt: str = "toml"):
    await require_auth(request)
    if fmt not in EXPORT_FORMATS:
        raise HTTPException(400, "Invalid format. Supported: " + ", ".join(EXPORT_FORMATS))
    clients = await asyncio.to_thread(parse_credentials)
    if not any(c["username"] == username for c in clients):
        raise HTTPException(404, "Not found")
    try:
        cfg = await asyncio.to_thread(export_client_config, username, fmt)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if cfg is None:
        raise HTTPException(502, "Configuration export failed. Is trusttunnel_endpoint installed?")
    return {"config": cfg, "format": fmt}


@app.put("/api/users/{username}/note")
async def set_user_note(username: str, request: Request):
    await require_auth(request)
    body = await request.json()
    note = str(body.get("note", "")).strip()[:200]

    def _mutate(db):
        notes = db.setdefault("user_notes", {})
        if note:
            notes[username] = note
        else:
            notes.pop(username, None)

    await asyncio.to_thread(update_panel_db, _mutate)
    return {"ok": True}


@app.get("/api/user-notes")
async def get_user_notes(request: Request):
    await require_auth(request)
    db = await asyncio.to_thread(load_panel_db)
    return {"notes": db.get("user_notes", {})}


@app.post("/api/users/import")
async def import_users(request: Request):
    await require_auth(request)
    body = await request.json()
    csv_data = body.get("csv", "")
    if not csv_data or not isinstance(csv_data, str):
        raise HTTPException(400, "CSV data required")
    rows = list(csv.reader(io.StringIO(csv_data.strip())))
    if len(rows) < 2:
        raise HTTPException(400, "No data rows")
    if len(rows) - 1 > MAX_IMPORT_ROWS:
        raise HTTPException(400, "Too many rows (max %d)" % MAX_IMPORT_ROWS)

    new_notes = {}

    def _mutate(clients):
        existing = {c["username"] for c in clients}
        added = 0
        for parts in rows[1:]:
            if len(parts) < 2:
                continue
            username = parts[0].strip().lstrip("'")
            password = parts[1].strip().lstrip("'")[:MAX_PASSWORD_LEN]
            if not _valid_username(username) or username in existing:
                continue
            enabled = parts[2].strip().lower() != "false" if len(parts) > 2 else True
            created = _clean_created(parts[3] if len(parts) > 3 else "")
            note = parts[4].strip().lstrip("'")[:200] if len(parts) > 4 else ""
            clients.append({"username": username, "password": password or generate_password(),
                            "enabled": enabled, "created_at": created})
            existing.add(username)
            if note:
                new_notes[username] = note
            added += 1
        return added

    added = await asyncio.to_thread(update_credentials, _mutate)
    if added:
        def _save_notes(db):
            db.setdefault("user_notes", {}).update(new_notes)

        await asyncio.to_thread(update_panel_db, _save_notes)
        schedule_reload("import_csv:%d users" % added)
    return {"ok": True, "added": added}
