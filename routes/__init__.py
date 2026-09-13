from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import config
from frontend import FRONTEND_HTML, APP_JS, APP_CSS

app = FastAPI(title="TrustTunnel Admin", docs_url=None, redoc_url=None)

_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


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
    if config._ssl_configured:
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


@app.get("/", response_class=HTMLResponse)
async def index():
    return FRONTEND_HTML


@app.get("/app.js")
async def app_js():
    # Served as a file (rather than inlined) so the CSP can drop 'unsafe-inline'.
    return Response(content=APP_JS, media_type="application/javascript; charset=utf-8")


@app.get("/app.css")
async def app_css():
    return Response(content=APP_CSS, media_type="text/css; charset=utf-8")


@app.get("/favicon.ico")
async def favicon():
    fav = _static_dir / "favicon.png"
    if fav.exists():
        return FileResponse(str(fav), media_type="image/png")
    return Response(status_code=204)


import routes.auth_routes  # noqa: E402, F401
import routes.user_routes  # noqa: E402, F401
import routes.monitoring_routes  # noqa: E402, F401
import routes.system_routes  # noqa: E402, F401
