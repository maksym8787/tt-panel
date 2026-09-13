from frontend.styles import CSS
from frontend.translations import TRANSLATIONS_JS
from frontend.core_js import PREAMBLE_JS, CORE_JS
from frontend.dashboard_js import DASHBOARD_JS
from frontend.monitor_js import MONITOR_JS
from frontend.users_js import USERS_JS
from frontend.settings_js import SETTINGS_JS
from frontend.init_js import INIT_JS

# JS and CSS are served as separate files (/app.js, /app.css) rather than inlined,
# so the Content-Security-Policy can forbid 'unsafe-inline' entirely.
APP_JS = (
    PREAMBLE_JS + TRANSLATIONS_JS + CORE_JS + DASHBOARD_JS
    + MONITOR_JS + USERS_JS + SETTINGS_JS + INIT_JS
)

APP_CSS = CSS

FRONTEND_HTML = (
    '<!DOCTYPE html>\n'
    '<html lang="en">\n'
    '<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5">\n'
    '<title>TrustTunnel Admin</title>\n'
    '<link rel="icon" type="image/png" sizes="64x64" href="/static/favicon.png?v=2">\n'
    '<link rel="icon" type="image/png" sizes="32x32" href="/static/icon-32.png?v=2">\n'
    '<link rel="apple-touch-icon" href="/static/apple-touch-icon.png?v=2">\n'
    '<link rel="stylesheet" href="/app.css">\n'
    '<script src="/static/qrcode.min.js" defer></script>\n'
    '<script src="/static/chart.umd.min.js" defer></script>\n'
    '<script src="/app.js" defer></script>\n'
    '</head>\n'
    '<body>\n'
    '<div id="root"></div>\n'
    '<div id="toast-host"></div>\n'
    '</body>\n'
    '</html>'
)
