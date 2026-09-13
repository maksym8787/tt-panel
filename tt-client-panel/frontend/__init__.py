from frontend.styles import STYLES
from frontend.translations import TRANSLATIONS
from frontend.core_js import CORE_JS
from frontend.servers_js import SERVERS_JS
from frontend.monitor_js import MONITOR_JS
from frontend.settings_js import SETTINGS_JS
from frontend.init_js import INIT_JS

# Served as separate files (/app.js, /app.css) so the CSP can forbid
# 'unsafe-inline'. INIT_JS must stay last: it kicks off the app.
APP_JS = "\n".join([TRANSLATIONS, CORE_JS, SERVERS_JS, MONITOR_JS, SETTINGS_JS, INIT_JS])

APP_CSS = STYLES

FRONTEND_HTML = (
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5">\n'
    '<title>TrustTunnel Client</title>\n'
    '<link rel="icon" type="image/png" sizes="64x64" href="/static/favicon.png?v=2">\n'
    '<link rel="stylesheet" href="/app.css">\n'
    '<script src="/static/chart.umd.min.js" defer></script>\n'
    '<script src="/app.js" defer></script>\n'
    '</head>\n<body>\n'
    '<div id="root"></div>\n'
    '<div id="toast-host"></div>\n'
    '</body>\n</html>\n'
)
