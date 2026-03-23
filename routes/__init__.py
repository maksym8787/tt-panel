from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import config
from frontend import FRONTEND_HTML

app = FastAPI(title="TrustTunnel Admin", docs_url=None, redoc_url=None)

_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


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
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    )
    return response


@app.get("/", response_class=HTMLResponse)
async def index():
    return FRONTEND_HTML


@app.get("/favicon.ico")
async def favicon():
    from fastapi.responses import FileResponse
    fav = Path(__file__).parent.parent / "static" / "favicon.png"
    if fav.exists():
        return FileResponse(str(fav), media_type="image/png")
    return Response(status_code=204)


import routes.auth_routes  # noqa: E402, F401
import routes.user_routes  # noqa: E402, F401
import routes.monitoring_routes  # noqa: E402, F401
import routes.system_routes  # noqa: E402, F401
