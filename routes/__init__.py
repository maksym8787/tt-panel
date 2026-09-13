from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import config
from frontend import (
    frontend_html, app_js, APP_CSS,
    DECOY_ROOT, DECOY_HEALTH, DECOY_NOT_FOUND, DECOY_METHOD, DECOY_OK_PATHS,
)

app = FastAPI(title="TrustTunnel Admin", docs_url=None, redoc_url=None)

_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
BASE = config.PANEL_BASE_PATH

# Operators can drop decoy.json or decoy.html next to panel.json; both are
# re-read when the file changes, so editing one needs no restart.
_DECOY_JSON = config.PANEL_DIR / "decoy.json"
_DECOY_HTML = config.PANEL_DIR / "decoy.html"
_decoy_cache = {"key": None, "body": None, "kind": None}


def _custom_decoy():
    """Returns (kind, body) for an operator-supplied page, or None."""
    for path, kind in ((_DECOY_JSON, "json"), (_DECOY_HTML, "html")):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        key = (str(path), mtime)
        if _decoy_cache["key"] != key:
            try:
                _decoy_cache.update(key=key, body=path.read_text(), kind=kind)
            except OSError:
                continue
        return _decoy_cache["kind"], _decoy_cache["body"]
    return None


def _decoy_response(request: Request) -> Response:
    """Answer like a plain JSON API: 200 on a few known paths, 404 elsewhere."""
    custom = _custom_decoy()
    if custom:
        kind, body = custom
        media = "application/json" if kind == "json" else "text/html; charset=utf-8"
        return Response(content=body, media_type=media, headers={"Cache-Control": "no-store"})

    headers = {"Cache-Control": "no-store"}
    if request.method not in ("GET", "HEAD"):
        return JSONResponse(DECOY_METHOD, status_code=405, headers=headers)
    path = request.url.path.rstrip("/") or "/"
    if path in DECOY_OK_PATHS:
        payload = DECOY_HEALTH if path != "/" else DECOY_ROOT
        return JSONResponse(payload, headers=headers)
    return JSONResponse(DECOY_NOT_FOUND, status_code=404, headers=headers)


@app.middleware("http")
async def base_path_gate(request: Request, call_next):
    """Serve the panel only under PANEL_BASE_PATH; decoy API everywhere else.

    The endpoint's reverse proxy does not strip the prefix, so we strip it here
    and let the normal routes match unchanged.
    """
    if not BASE:
        return await call_next(request)
    path = request.url.path
    if path == BASE or path.startswith(BASE + "/"):
        stripped = path[len(BASE):] or "/"
        request.scope["path"] = stripped
        request.scope["raw_path"] = stripped.encode("utf-8")
        return await call_next(request)
    return _decoy_response(request)


@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    """Reject cross-site state-changing requests.

    Session auth is cookie-based, so SameSite is the first line of defence; this
    is the second. Requests carrying neither header (curl, scripts) are allowed —
    browsers always send at least one of them on cross-origin requests.
    """
    if request.method not in _SAFE_METHODS:
        site = request.headers.get("sec-fetch-site")
        if site is not None:
            if site not in ("same-origin", "none"):
                return JSONResponse({"detail": "Cross-site request blocked"}, status_code=403)
        else:
            origin = request.headers.get("origin")
            if origin:
                host = request.headers.get("host", "")
                if urlsplit(origin).netloc != host:
                    return JSONResponse({"detail": "Cross-site request blocked"}, status_code=403)
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if config._ssl_configured or config.BEHIND_PROXY:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "font-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'; "
        "form-action 'none'; "
        "object-src 'none'"
    )
    return response


_INDEX_HTML = frontend_html(BASE)
_APP_JS = app_js(BASE)


@app.get("/", response_class=HTMLResponse)
async def index():
    return _INDEX_HTML


@app.get("/app.js")
async def serve_app_js():
    # Served as a file (rather than inlined) so the CSP can drop 'unsafe-inline'.
    return Response(content=_APP_JS, media_type="application/javascript; charset=utf-8")


@app.get("/app.css")
async def app_css():
    return Response(content=APP_CSS, media_type="text/css; charset=utf-8")


@app.get("/favicon.ico")
async def favicon():
    fav = _static_dir / "favicon.png"
    if fav.exists():
        return FileResponse(str(fav), media_type="image/png")
    return Response(status_code=204)


import routes.transport_routes  # noqa: E402, F401
import routes.auth_routes  # noqa: E402, F401
import routes.user_routes  # noqa: E402, F401
import routes.monitoring_routes  # noqa: E402, F401
import routes.system_routes  # noqa: E402, F401
