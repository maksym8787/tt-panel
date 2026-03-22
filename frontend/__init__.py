from frontend.styles import CSS
from frontend.translations import TRANSLATIONS_JS
from frontend.core_js import PREAMBLE_JS, CORE_JS
from frontend.dashboard_js import DASHBOARD_JS
from frontend.monitor_js import MONITOR_JS
from frontend.users_js import USERS_JS
from frontend.settings_js import SETTINGS_JS
from frontend.init_js import INIT_JS

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
    '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" crossorigin="anonymous">\n'
    '<script src="/static/qrcode.min.js" defer></script>\n'
    '<script src="/static/chart.umd.min.js" defer></script>\n'
    '<style>\n' + CSS + '</style>\n'
    '</head>\n'
    '<body>\n'
    '<div id="root"></div>\n'
    '<script>\n' + PREAMBLE_JS + TRANSLATIONS_JS + CORE_JS + DASHBOARD_JS + MONITOR_JS + USERS_JS + SETTINGS_JS + INIT_JS + '</script>\n'
    '</body>\n'
    '</html>'
)
