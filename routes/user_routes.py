import asyncio
import re
from datetime import datetime

from fastapi import HTTPException, Request
from fastapi.responses import Response

from auth import load_panel_db, save_panel_db, require_auth
from services import (
    parse_credentials, write_credentials, export_client_config,
    generate_password, schedule_reload,
)
from routes import app


@app.get("/api/users")
async def list_users(request: Request):
    await require_auth(request)
    clients = await asyncio.to_thread(parse_credentials)
    return {"users": [{"username": c["username"], "password": c.get("password", ""), "enabled": c.get("enabled", True), "created_at": c.get("created_at", "")} for c in clients]}


@app.post("/api/users")
async def add_user(request: Request):
    await require_auth(request)
    body = await request.json()
    username = body.get("username", "").strip()
    password = body.get("password", "").strip() or generate_password()
    if not username:
        raise HTTPException(400, "Username required")
    if not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', username):
        raise HTTPException(400, "Username must be 1-64 chars: letters, digits, hyphens, underscores")
    clients = await asyncio.to_thread(parse_credentials)
    if any(c["username"] == username for c in clients):
        raise HTTPException(400, "User exists")
    clients.append({
        "username": username, "password": password,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "enabled": True,
    })
    await asyncio.to_thread(write_credentials, clients)
    schedule_reload("user_add:" + username)
    return {"ok": True, "username": username, "password": password}


@app.put("/api/users/{username}")
async def update_user(username: str, request: Request):
    await require_auth(request)
    body = await request.json()
    pw = body.get("password", "").strip()
    if not pw:
        raise HTTPException(400, "Password required")
    clients = await asyncio.to_thread(parse_credentials)
    found = False
    for c in clients:
        if c["username"] == username:
            c["password"] = pw
            found = True
            break
    if not found:
        raise HTTPException(404, "Not found")
    await asyncio.to_thread(write_credentials, clients)
    schedule_reload("password_change:" + username)
    return {"ok": True}


@app.delete("/api/users/{username}")
async def delete_user(username: str, request: Request):
    await require_auth(request)
    clients = await asyncio.to_thread(parse_credentials)
    new = [c for c in clients if c["username"] != username]
    if len(new) == len(clients):
        raise HTTPException(404, "Not found")
    await asyncio.to_thread(write_credentials, new)
    schedule_reload("user_delete:" + username)
    return {"ok": True}


@app.put("/api/users/{username}/toggle")
async def toggle_user(username: str, request: Request):
    await require_auth(request)
    clients = await asyncio.to_thread(parse_credentials)
    found = False
    for c in clients:
        if c["username"] == username:
            c["enabled"] = not c.get("enabled", True)
            found = True
            break
    if not found:
        raise HTTPException(404, "Not found")
    await asyncio.to_thread(write_credentials, clients)
    action = "user_enable" if c["enabled"] else "user_disable"
    schedule_reload(action + ":" + username)
    return {"ok": True, "enabled": c["enabled"]}


@app.get("/api/users/{username}/config")
async def get_user_config(username: str, request: Request, fmt: str = "toml"):
    await require_auth(request)
    if fmt not in ("toml", "json", "deeplink"):
        raise HTTPException(400, "Invalid format")
    clients = await asyncio.to_thread(parse_credentials)
    if not any(c["username"] == username for c in clients):
        raise HTTPException(404)
    cfg = await asyncio.to_thread(export_client_config, username, fmt)
    return {"config": cfg, "format": fmt}


@app.put("/api/users/{username}/note")
async def set_user_note(username: str, request: Request):
    await require_auth(request)
    body = await request.json()
    note = body.get("note", "").strip()[:200]
    db = await asyncio.to_thread(load_panel_db)
    notes = db.get("user_notes", {})
    if note:
        notes[username] = note
    else:
        notes.pop(username, None)
    db["user_notes"] = notes
    await asyncio.to_thread(save_panel_db, db)
    return {"ok": True}


@app.get("/api/user-notes")
async def get_user_notes(request: Request):
    await require_auth(request)
    db = await asyncio.to_thread(load_panel_db)
    return {"notes": db.get("user_notes", {})}


@app.get("/api/users/export")
async def export_users(request: Request):
    await require_auth(request)
    clients = await asyncio.to_thread(parse_credentials)
    db = await asyncio.to_thread(load_panel_db)
    notes = db.get("user_notes", {})
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["username", "password", "enabled", "created_at", "note"])
    for c in clients:
        writer.writerow([c["username"], c["password"], c.get("enabled", True), c.get("created_at", ""), notes.get(c["username"], "")])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )


@app.post("/api/users/import")
async def import_users(request: Request):
    await require_auth(request)
    body = await request.json()
    csv_data = body.get("csv", "")
    if not csv_data:
        raise HTTPException(400, "CSV data required")
    import csv, io
    reader = csv.reader(io.StringIO(csv_data.strip()))
    rows = list(reader)
    if len(rows) < 2:
        raise HTTPException(400, "No data rows")
    clients = await asyncio.to_thread(parse_credentials)
    existing = {c["username"] for c in clients}
    db = await asyncio.to_thread(load_panel_db)
    notes = db.get("user_notes", {})
    added = 0
    for parts in rows[1:]:
        if len(parts) < 2:
            continue
        username = parts[0].strip()
        password = parts[1].strip()
        if not username or not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', username):
            continue
        if username in existing:
            continue
        enabled = parts[2].strip().lower() != "false" if len(parts) > 2 else True
        created = parts[3].strip() if len(parts) > 3 else datetime.now().isoformat(timespec="seconds")
        note = parts[4].strip() if len(parts) > 4 else ""
        clients.append({"username": username, "password": password or generate_password(),
                        "enabled": enabled, "created_at": created or datetime.now().isoformat(timespec="seconds")})
        existing.add(username)
        if note:
            notes[username] = note
        added += 1
    if added > 0:
        await asyncio.to_thread(write_credentials, clients)
        db["user_notes"] = notes
        await asyncio.to_thread(save_panel_db, db)
        schedule_reload("import_csv:" + str(added) + " users")
    return {"ok": True, "added": added}
