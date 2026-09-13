from frontend.styles import CSS
from frontend.translations import TRANSLATIONS_JS
from frontend.core_js import PREAMBLE_JS, CORE_JS
from frontend.dashboard_js import DASHBOARD_JS
from frontend.monitor_js import MONITOR_JS
from frontend.users_js import USERS_JS
from frontend.settings_js import SETTINGS_JS
from frontend.init_js import INIT_JS

# JS and CSS are served as separate files (/app.js, /app.css) rather than inlined,
# so the Content-Security-Policy can forbid 'unsafe-inline'.
_APP_BODY = (
    PREAMBLE_JS + TRANSLATIONS_JS + CORE_JS + DASHBOARD_JS
    + MONITOR_JS + USERS_JS + SETTINGS_JS + INIT_JS
)

APP_CSS = CSS

# Everything outside the panel's prefix answers like an ordinary JSON backend:
# a terse service banner on the root, a health endpoint, and 404/405 elsewhere.
# That is duller to a scanner than any HTML page and invites no exploration. It
# names no real company or product and asserts nothing about anyone. Drop a
# decoy.json or decoy.html next to panel.json to replace it.
DECOY_ROOT = {"service": "api", "status": "ok", "version": "1"}
DECOY_HEALTH = {"status": "healthy"}
DECOY_NOT_FOUND = {"error": "not_found", "message": "The requested resource does not exist."}
DECOY_METHOD = {"error": "method_not_allowed"}
# Paths that answer 200 instead of 404, as a real service would.
DECOY_OK_PATHS = {"/", "/health", "/healthz", "/status", "/ping"}


def app_js(base: str = "") -> str:
    """The bundle, told where it is mounted so every URL it builds is prefixed."""
    return "var BASE=%s;\n%s" % (_js_string(base), _APP_BODY)


def _js_string(value: str) -> str:
    return '"%s"' % value.replace("\\", "\\\\").replace('"', '\\"')


def frontend_html(base: str = "") -> str:
    b = base or ""
    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5">\n'
        '<title>TrustTunnel Admin</title>\n'
        '<meta name="robots" content="noindex,nofollow">\n'
        f'<link rel="icon" type="image/png" sizes="64x64" href="{b}/static/favicon.png?v=2">\n'
        f'<link rel="icon" type="image/png" sizes="32x32" href="{b}/static/icon-32.png?v=2">\n'
        f'<link rel="apple-touch-icon" href="{b}/static/apple-touch-icon.png?v=2">\n'
        f'<link rel="stylesheet" href="{b}/app.css">\n'
        f'<script src="{b}/static/qrcode.min.js" defer></script>\n'
        f'<script src="{b}/static/chart.umd.min.js" defer></script>\n'
        f'<script src="{b}/app.js" defer></script>\n'
        '</head>\n'
        '<body>\n'
        '<div id="root"></div>\n'
        '<div id="toast-host"></div>\n'
        '</body>\n'
        '</html>'
    )


# Backwards-compatible module-level values for a panel served at the root.
APP_JS = app_js("")
FRONTEND_HTML = frontend_html("")
