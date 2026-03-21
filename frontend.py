FRONTEND_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5">
<title>TrustTunnel Admin</title>
<link rel="icon" type="image/png" sizes="64x64" href="/static/favicon.png?v=2">
<link rel="icon" type="image/png" sizes="32x32" href="/static/icon-32.png?v=2">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png?v=2">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" crossorigin="anonymous">
<script src="/static/qrcode.min.js" defer></script>
<script src="/static/chart.umd.min.js" defer></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#06080b;--sf:#0c1018;--sf2:#131a24;--sf3:#1a2332;
  --bd:#1e2a3a;--bd2:#2a3a4e;
  --tx:#e2e8f0;--tx2:#8899aa;--tx3:#556677;
  --ac:#3b9eff;--ac2:#2076d6;--ac3:#1a5faa;
  --gn:#22c55e;--gn2:#166534;--gnbg:rgba(34,197,94,.08);
  --rd:#ef4444;--rd2:#7f1d1d;--rdbg:rgba(239,68,68,.08);
  --or:#f59e0b;--or2:#78350f;--orbg:rgba(245,158,11,.08);
  --cy:#06b6d4;--cybg:rgba(6,182,212,.08);
  --vi:#a78bfa;--vibg:rgba(167,139,250,.08);
  --r:12px;--r2:8px;
  --f:'DM Sans',system-ui,sans-serif;--m:'JetBrains Mono',monospace;
  --shadow:0 1px 3px rgba(0,0,0,.3),0 4px 12px rgba(0,0,0,.2);
  --glow:0 0 20px rgba(59,158,255,.08);
}
[data-theme="light"]{
  --bg:#f5f7fa;--sf:#ffffff;--sf2:#f0f2f5;--sf3:#e8eaed;
  --bd:#d0d5dd;--bd2:#b0b8c4;
  --tx:#1a1a2e;--tx2:#4a5568;--tx3:#718096;
  --ac:#2563eb;--ac2:#1d4ed8;--ac3:#1e40af;
  --gn:#16a34a;--gn2:#15803d;--gnbg:rgba(22,163,74,.08);
  --rd:#dc2626;--rd2:#fecaca;--rdbg:rgba(220,38,38,.06);
  --or:#d97706;--or2:#fef3c7;--orbg:rgba(217,119,6,.06);
  --cy:#0891b2;--cybg:rgba(8,145,178,.06);
  --vi:#7c3aed;--vibg:rgba(124,58,237,.06);
  --shadow:0 1px 3px rgba(0,0,0,.08),0 4px 12px rgba(0,0,0,.05);
  --glow:0 0 20px rgba(37,99,235,.06);
}
[data-theme="system"]{/* inherits :root dark by default */}
@media(prefers-color-scheme:light){
  [data-theme="system"]{
    --bg:#f5f7fa;--sf:#ffffff;--sf2:#f0f2f5;--sf3:#e8eaed;
    --bd:#d0d5dd;--bd2:#b0b8c4;
    --tx:#1a1a2e;--tx2:#4a5568;--tx3:#718096;
    --ac:#2563eb;--ac2:#1d4ed8;--ac3:#1e40af;
    --gn:#16a34a;--gn2:#15803d;--gnbg:rgba(22,163,74,.08);
    --rd:#dc2626;--rd2:#fecaca;--rdbg:rgba(220,38,38,.06);
    --or:#d97706;--or2:#fef3c7;--orbg:rgba(217,119,6,.06);
    --cy:#0891b2;--cybg:rgba(8,145,178,.06);
    --vi:#7c3aed;--vibg:rgba(124,58,237,.06);
    --shadow:0 1px 3px rgba(0,0,0,.08),0 4px 12px rgba(0,0,0,.05);
    --glow:0 0 20px rgba(37,99,235,.06);
  }
}
[data-theme="light"] .logo-i,[data-theme="system"] .logo-i{color:#1a1a2e}
@media(prefers-color-scheme:light){[data-theme="system"] .logo-i{color:#1a1a2e}}
.logo-img{transition:filter .3s;object-fit:contain}
[data-theme="dark"] .logo-img{filter:brightness(0) invert(1)}
@media(prefers-color-scheme:dark){[data-theme="system"] .logo-img{filter:brightness(0) invert(1)}}
[data-theme="light"] .toast-ok{background:#f0fdf4;border:1px solid #86efac;color:#16a34a}
[data-theme="light"] .toast-err{background:#fef2f2;border:1px solid #fca5a5;color:#dc2626}
@media(prefers-color-scheme:light){
  [data-theme="system"] .toast-ok{background:#f0fdf4;border:1px solid #86efac;color:#16a34a}
  [data-theme="system"] .toast-err{background:#fef2f2;border:1px solid #fca5a5;color:#dc2626}
}
[data-theme="light"] .lb{background:#f8f9fa;color:#4a5568}
@media(prefers-color-scheme:light){[data-theme="system"] .lb{background:#f8f9fa;color:#4a5568}}
[data-theme="light"] .btn-d{background:#fef2f2;border-color:#fca5a5;color:#dc2626}
[data-theme="light"] .btn-d:hover{background:#fee2e2}
@media(prefers-color-scheme:light){
  [data-theme="system"] .btn-d{background:#fef2f2;border-color:#fca5a5;color:#dc2626}
  [data-theme="system"] .btn-d:hover{background:#fee2e2}
}
[data-theme="light"] ::-webkit-scrollbar-thumb{background:#d0d5dd}
@media(prefers-color-scheme:light){[data-theme="system"] ::-webkit-scrollbar-thumb{background:#d0d5dd}}
/* Theme toggle buttons */
.tg{display:inline-flex;gap:1px;background:var(--sf);border:1px solid var(--bd);border-radius:6px;padding:2px;margin-right:6px}
.tg button{padding:3px 7px;border:none;border-radius:4px;background:transparent;color:var(--tx3);cursor:pointer;font-size:11px;transition:.15s;line-height:1}
.tg button:hover{color:var(--tx2)}
.tg button.on{background:var(--sf2);color:var(--ac);box-shadow:0 1px 3px rgba(0,0,0,.15)}
.lg{display:inline-flex;gap:1px;background:var(--sf);border:1px solid var(--bd);border-radius:6px;padding:2px;margin-right:6px}
.lg button{padding:3px 7px;border:none;border-radius:4px;background:transparent;color:var(--tx3);cursor:pointer;font-size:11px;font-weight:600;transition:.15s;line-height:1}
.lg button:hover{color:var(--tx2)}
.lg button.on{background:var(--sf2);color:var(--ac);box-shadow:0 1px 3px rgba(0,0,0,.15)}
body{background:var(--bg);color:var(--tx);font-family:var(--f);min-height:100vh;-webkit-font-smoothing:antialiased}
input,textarea,select,button{font-family:inherit;font-size:inherit}
::-webkit-scrollbar{width:5px;height:5px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--bd);border-radius:3px}
::selection{background:var(--ac2);color:#fff}

.app{max-width:1000px;margin:0 auto;padding:16px}
@media(min-width:768px){.app{padding:24px 32px}}

/* Header */
.hdr{display:flex;align-items:center;justify-content:space-between;padding:14px 0 18px;margin-bottom:16px;gap:8px;flex-wrap:wrap}
.logo{display:flex;align-items:center;gap:12px}
.logo-i{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center}
.logo-i svg{width:60%;height:60%}
.logo-t{font-size:17px;font-weight:700;letter-spacing:-.03em}
.logo-s{font-size:11px;color:var(--tx3);font-family:var(--m)}

/* Tabs */
.tabs{display:flex;gap:2px;margin-bottom:18px;background:var(--sf);border-radius:10px;padding:3px;border:1px solid var(--bd);overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:1;min-width:0;padding:8px 10px;border-radius:8px;border:none;background:transparent;color:var(--tx3);cursor:pointer;font-size:12px;font-weight:600;white-space:nowrap;transition:all .2s;text-align:center}
@media(max-width:480px){.tab{padding:8px 6px;font-size:11px;flex:0 0 auto}}
.tab:hover{color:var(--tx2)}
.tab.on{background:var(--sf2);color:var(--tx);box-shadow:var(--shadow)}

/* Cards */
.card{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:18px;margin-bottom:14px;box-shadow:var(--shadow)}
.card-t{font-size:12px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;color:var(--tx2);text-transform:uppercase;letter-spacing:.05em}
.card-t .right{display:flex;gap:4px}

/* Stats grid */
.grid{display:grid;gap:10px}.grid2{grid-template-columns:1fr 1fr}.grid3{grid-template-columns:1fr 1fr 1fr}.grid4{grid-template-columns:repeat(4,1fr)}
@media(max-width:640px){.grid3,.grid4{grid-template-columns:1fr 1fr}.grid2{grid-template-columns:1fr}}
@media(max-width:400px){.grid3,.grid4{grid-template-columns:1fr}}

/* Stat cards */
.stat{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:14px 16px;position:relative;overflow:hidden;transition:border-color .2s}
.stat:hover{border-color:var(--bd2)}
.stat-l{font-size:10px;color:var(--tx3);text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin-bottom:6px}
.stat-v{font-size:20px;font-weight:700;font-family:var(--m);letter-spacing:-.02em;line-height:1.2}
.stat-sub{font-size:10px;color:var(--tx3);font-family:var(--m);margin-top:3px}
.stat-v.on{color:var(--gn)}.stat-v.off{color:var(--rd)}.stat-v.warn{color:var(--or)}
.stat-v.ac{color:var(--ac)}

/* Colored stat backgrounds */
.stat-green{background:var(--gnbg);border-color:rgba(34,197,94,.15)}
.stat-red{background:var(--rdbg);border-color:rgba(239,68,68,.15)}
.stat-orange{background:var(--orbg);border-color:rgba(245,158,11,.15)}
.stat-cyan{background:var(--cybg);border-color:rgba(6,182,212,.15)}
.stat-violet{background:var(--vibg);border-color:rgba(167,139,250,.15)}

/* Buttons */
.btn{display:inline-flex;align-items:center;gap:5px;padding:7px 14px;border-radius:var(--r2);border:1px solid var(--bd);background:var(--sf2);color:var(--tx);font-size:12px;font-weight:500;cursor:pointer;transition:all .15s;white-space:nowrap}
.btn:hover{border-color:var(--bd2);background:var(--sf3)}
.btn:disabled{opacity:.5;cursor:not-allowed}
.btn-p{background:var(--ac2);border-color:var(--ac2);color:#fff}.btn-p:hover{background:var(--ac)}
.btn-d{background:var(--rd2);border-color:#9e2a2a;color:#fca5a5}.btn-d:hover{background:#991b1b}
.btn-sm{padding:4px 10px;font-size:11px;border-radius:6px}
.btn-xs{padding:3px 8px;font-size:10px;border-radius:5px}
.btn-ghost{background:transparent;border-color:transparent}.btn-ghost:hover{background:var(--sf2);border-color:var(--bd)}
.bg{display:flex;gap:6px;flex-wrap:wrap;align-items:center}

/* (#16) Mobile touch targets */
@media(max-width:640px){.btn-xs{min-height:44px;padding:6px 12px;font-size:11px}}

/* Period selector */
.periods{display:flex;gap:2px;background:var(--bg);border-radius:7px;padding:2px;border:1px solid var(--bd)}
.per{padding:4px 10px;border-radius:5px;border:none;background:transparent;color:var(--tx3);cursor:pointer;font-size:10px;font-weight:600;font-family:var(--m);transition:.15s}
.per:hover{color:var(--tx2)}.per.on{background:var(--sf2);color:var(--ac);box-shadow:0 1px 4px rgba(0,0,0,.3)}

/* Inputs */
.input{width:100%;padding:10px 14px;border-radius:var(--r2);border:1px solid var(--bd);background:var(--bg);color:var(--tx);font-size:13px;outline:none;transition:border-color .2s}
.input:focus{border-color:var(--ac);box-shadow:0 0 0 3px rgba(59,158,255,.1)}
textarea.input{resize:vertical;min-height:100px}.input-m{font-family:var(--m);font-size:12px}
.fg{margin-bottom:14px}.fl{display:block;font-size:10px;font-weight:600;color:var(--tx3);margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em}

/* User cards */
.uc{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);margin-bottom:8px;transition:border-color .2s;gap:10px}
.uc:hover{border-color:var(--bd2)}
.ui{display:flex;align-items:center;gap:8px;min-width:0;flex-wrap:wrap}
@media(max-width:640px){.uc{flex-direction:column;align-items:stretch}.uact{justify-content:flex-start;flex-wrap:wrap}}
.ua{width:36px;height:36px;border-radius:9px;background:linear-gradient(135deg,var(--ac3),var(--ac2));display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;color:#fff;flex-shrink:0}
.uc-dis{opacity:.55;border-style:dashed}
.ua-dis{background:var(--tx3)!important}
.un-dis{text-decoration:line-through;color:var(--tx3)}
.un{font-weight:600;font-size:13px}.up{font-family:var(--m);font-size:11px;color:var(--tx3)}
.uact{display:flex;gap:4px;flex-shrink:0}

/* Code/log blocks */
.cb{background:var(--bg);border:1px solid var(--bd);border-radius:var(--r2);padding:14px;font-family:var(--m);font-size:11px;color:var(--tx2);white-space:pre-wrap;word-break:break-all;max-height:300px;overflow:auto;line-height:1.6}
.lb{background:#000;border-radius:var(--r2);padding:14px;font-family:var(--m);font-size:10px;color:var(--tx3);white-space:pre-wrap;word-break:break-all;max-height:500px;overflow:auto;line-height:1.6}

/* Modal (#19 accessible) */
.mo{position:fixed;inset:0;background:rgba(0,0,0,.75);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;z-index:100;padding:16px}
.md{background:var(--sf);border:1px solid var(--bd);border-radius:16px;padding:24px;width:calc(100% - 32px);max-width:480px;max-height:90vh;overflow:auto;box-shadow:0 8px 40px rgba(0,0,0,.5)}
@media(max-width:480px){.md{padding:16px;border-radius:12px}}
.md-t{font-size:16px;font-weight:700;margin-bottom:16px}

/* Toast */
.toast{position:fixed;top:16px;right:16px;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:500;z-index:9999;box-shadow:0 4px 20px rgba(0,0,0,.4);animation:slideIn .2s}
@keyframes slideIn{from{transform:translateX(20px);opacity:0}to{transform:none;opacity:1}}
.toast-ok{background:#052e16;border:1px solid #166534;color:var(--gn)}.toast-err{background:#450a0a;border:1px solid #991b1b;color:var(--rd)}

/* Login */
.lw{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;background:radial-gradient(ellipse at 50% 30%,rgba(59,158,255,.05),transparent 60%)}
.lc{width:100%;max-width:380px;padding:32px;background:var(--sf);border:1px solid var(--bd);border-radius:18px;box-shadow:var(--glow),var(--shadow)}
.lt{font-size:22px;font-weight:700;text-align:center;margin-bottom:6px;letter-spacing:-.02em}
.ls{font-size:12px;color:var(--tx3);text-align:center;margin-bottom:24px}

/* Tables */
.tbl-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tbl{width:100%;border-collapse:collapse;font-size:11px}
.tbl th{text-align:left;padding:8px 10px;border-bottom:1px solid var(--bd);color:var(--tx3);font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.05em;background:var(--bg)}
.tbl td{padding:7px 10px;border-bottom:1px solid rgba(30,42,58,.5);color:var(--tx2);font-family:var(--m);font-size:11px}
.tbl tr:hover td{background:rgba(59,158,255,.03)}
.tbl th:first-child{border-radius:6px 0 0 0}.tbl th:last-child{border-radius:0 6px 0 0}

/* Badge */
.badge{display:inline-block;padding:2px 8px;border-radius:5px;font-size:10px;font-weight:600;font-family:var(--m)}
.b-gn{background:rgba(34,197,94,.12);color:var(--gn)}
.b-rd{background:rgba(239,68,68,.12);color:var(--rd)}
.b-or{background:rgba(245,158,11,.12);color:var(--or)}
.b-bl{background:rgba(59,158,255,.12);color:var(--ac)}

/* Online user dot */
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;flex-shrink:0}
.dot-on{background:var(--gn);box-shadow:0 0 6px var(--gn)}
.dot-idle{background:var(--or);box-shadow:0 0 6px rgba(245,158,11,.4)}

/* Chart containers */
.chart-wrap{position:relative;height:180px}
@media(max-width:640px){.chart-wrap{height:150px}}

/* QR */
.qc{display:flex;flex-direction:column;align-items:center;gap:12px;padding:20px}
.qr{background:#fff;padding:16px;border-radius:12px}

/* Section divider */
.section-gap{margin-bottom:18px}

/* Fade in animation */
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.fade-in{animation:fadeIn .3s ease-out}

/* Pulse for live indicator */
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.pulse{animation:pulse 2s ease-in-out infinite}

@keyframes spin{to{transform:rotate(360deg)}}
.spinner{width:16px;height:16px;border:2px solid var(--bd);border-top-color:var(--ac);border-radius:50%;animation:spin .6s linear infinite}
.spinner-lg{width:28px;height:28px;border-width:2.5px}
.loading-box{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:60px 0;color:var(--tx3);font-size:13px;font-weight:500;letter-spacing:.02em}

/* (#17) Apply changes banner */
.apply-bar{background:var(--orbg);border:1px solid rgba(245,158,11,.25);border-radius:var(--r2);padding:10px 16px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;font-size:12px;color:var(--or)}
</style>
</head>
<body>
<div id="root"></div>
<script>
var LOGO_ICON='/static/favicon.png';
var LOGO_FULL='/static/logo-full.png';
var A='/api';
var T={
en:{
  dashboard:'Dashboard',monitor:'Monitor',users:'Users',settings:'Settings',logs:'Logs',
  service:'Service',online:'Online',offline:'Offline',running:'Running',
  tcp_sessions:'TCP sessions',users_configured:'users configured',
  mem_cpu:'Memory / CPU',certificate:'Certificate',
  today:'Today',this_week:'This week',
  download:'Download',upload:'Upload',peak_sessions:'Peak sessions',
  connections:'Connections',dl_restart:'Download (since restart)',ul_restart:'Upload (since restart)',
  disk:'Disk',uptime:'Uptime',vps_resources:'VPS Resources',traffic_hourly:'Hourly traffic',
  sockets:'Sockets (TCP/UDP)',controls:'Controls',refresh:'Refresh',
  restart:'Restart',reload_tls:'Reload TLS',stop:'Stop',renew_cert:'Renew cert',
  server_info:'Server info',domain:'Domain',server_uptime:'Server uptime',service_uptime:'Service uptime',
  monitoring:'Monitoring',active_sessions:'Active sessions',now:'now',
  bandwidth:'Traffic (Download / Upload)',cpu_memory:'CPU & Memory',
  online_users:'Online users',sessions:'sessions',
  recently_active:'Recently active (1h)',connection_log:'Connection log',
  no_conn_data:'No connection data yet',
  top_destinations:'Top destinations (by domain)',
  traffic_per_client:'Traffic per client IP',port_breakdown:'Port breakdown',
  unique_ips:'Unique IPs',unique_ips_label:'Unique IPs',user_connections:'User connections',no_client_data:'No client data',no_port_data:'No port data',
  client_ip:'Client IP',agent:'Agent',conn:'Conn',last_seen:'Last seen',
  port:'Port',svc_name:'Service',count:'Count',destination:'Destination',
  time:'Time',ip:'IP',user_agent:'User agent',event:'Event',
  sessions_active_no_ip:'Sessions active but no IP data from logs yet',
  no_active_conn:'No active connections',
  user:'user',users_pl:'users',add_user:'+ Add user',
  active_ip:'active IP',active_ips:'active IPs',
  search_users:'Search users...',
  sort_name_az:'Name A\u2192Z',sort_name_za:'Name Z\u2192A',sort_date_new:'Newest first',sort_date_old:'Oldest first',
  add_vpn_user:'Add VPN user',username:'Username',
  password:'Password',password_empty_auto:'Password (empty = auto-generate)',
  create:'Create',cancel:'Cancel',close:'Close',copy:'Copy',copied:'Copied!',
  config:'Config',
  delete_user:'Delete user',delete_confirm:'Are you sure you want to delete',
  confirm:'Confirm',
  change_password:'Change password',new_password:'New password',save:'Save',
  renew_confirm:'Renew certificate? Service will restart.',
  new_admin_password:'New admin password (6+ chars)',
  read_only:'read-only',
  service_logs:'Service logs',click_refresh:'Click Refresh to load logs',
  initial_setup:'Initial Setup',create_admin_pw:'Create admin password',
  enter_admin_pw:'Enter admin password',create_password:'Create password',sign_in:'Sign in',
  loading:'Loading...',render_error:'Render error',
  apply_changes:'Apply changes',pending_restart:'Configuration changes pending restart',
  password_btn:'Password',logout:'Logout',
  changed_relogin:'Password changed, please re-login',
  deleted:'Deleted',changed:'Changed',saved:'Saved',
  user_created:'User created',pass_label:'pass',
  qr_not_loaded:'QR library not loaded',
  theme_dark:'Dark',theme_light:'Light',theme_system:'System',
  s_ago:'s ago',m_ago:'m ago',h_ago:'h ago',d_ago:'d ago',
  ip_address:'IP address',location:'Location',isp:'ISP',destinations:'Destinations',
  svc_action_ok:'OK',no_cert:'No cert',auto_renew:'Auto-renew enabled',
  change:'Change',config_for:'Config',
  btn_config:'Config',btn_qr:'QR',btn_pass:'Password',btn_del:'Delete',
  btn_enable:'Enable',btn_disable:'Disable',created_label:'Created',
  user_enabled:'Enabled',user_disabled:'Disabled',
  show_more:'Show more',show_less:'Show less',of_total:'of',
  prev_page:'Prev',next_page:'Next'
},
ru:{
  dashboard:'\u041f\u0430\u043d\u0435\u043b\u044c',monitor:'\u041c\u043e\u043d\u0438\u0442\u043e\u0440',users:'\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438',settings:'\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438',logs:'\u041b\u043e\u0433\u0438',
  service:'\u0421\u0435\u0440\u0432\u0438\u0441',online:'\u0410\u043a\u0442\u0438\u0432\u0435\u043d',offline:'\u041e\u0442\u043a\u043b\u044e\u0447\u0435\u043d',running:'\u0420\u0430\u0431\u043e\u0442\u0430\u0435\u0442',
  tcp_sessions:'TCP \u0441\u0435\u0441\u0441\u0438\u0438',users_configured:'\u043f\u043e\u043b\u044c\u0437. \u043d\u0430\u0441\u0442\u0440\u043e\u0435\u043d\u043e',
  mem_cpu:'\u041f\u0430\u043c\u044f\u0442\u044c / CPU',certificate:'\u0421\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442',
  today:'\u0421\u0435\u0433\u043e\u0434\u043d\u044f',this_week:'\u0417\u0430 \u043d\u0435\u0434\u0435\u043b\u044e',
  download:'\u0421\u043a\u0430\u0447\u0430\u043d\u043e',upload:'\u0417\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u043e',peak_sessions:'\u041f\u0438\u043a \u0441\u0435\u0441\u0441\u0438\u0439',
  connections:'\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f',dl_restart:'\u0421\u043a\u0430\u0447\u0430\u043d\u043e (\u0441 \u0440\u0435\u0441\u0442\u0430\u0440\u0442\u0430)',ul_restart:'\u0417\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u043e (\u0441 \u0440\u0435\u0441\u0442\u0430\u0440\u0442\u0430)',
  disk:'\u0414\u0438\u0441\u043a',uptime:'\u0410\u043f\u0442\u0430\u0439\u043c',vps_resources:'\u0420\u0435\u0441\u0443\u0440\u0441\u044b VPS',traffic_hourly:'\u0422\u0440\u0430\u0444\u0438\u043a \u043f\u043e \u0447\u0430\u0441\u0430\u043c',
  sockets:'\u0421\u043e\u043a\u0435\u0442\u044b (TCP/UDP)',controls:'\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435',refresh:'\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c',
  restart:'\u041f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u043a',reload_tls:'\u041f\u0435\u0440\u0435\u0437\u0430\u0433\u0440. TLS',stop:'\u0421\u0442\u043e\u043f',renew_cert:'\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u0435\u0440\u0442.',
  server_info:'\u0418\u043d\u0444\u043e\u0440\u043c\u0430\u0446\u0438\u044f \u043e \u0441\u0435\u0440\u0432\u0435\u0440\u0435',domain:'\u0414\u043e\u043c\u0435\u043d',server_uptime:'\u0410\u043f\u0442\u0430\u0439\u043c \u0441\u0435\u0440\u0432\u0435\u0440\u0430',service_uptime:'\u0410\u043f\u0442\u0430\u0439\u043c \u0441\u0435\u0440\u0432\u0438\u0441\u0430',
  monitoring:'\u041c\u043e\u043d\u0438\u0442\u043e\u0440\u0438\u043d\u0433',active_sessions:'\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0435 \u0441\u0435\u0441\u0441\u0438\u0438',now:'\u0441\u0435\u0439\u0447\u0430\u0441',
  bandwidth:'\u0422\u0440\u0430\u0444\u0438\u043a (\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 / \u041e\u0442\u0434\u0430\u0447\u0430)',cpu_memory:'CPU \u0438 \u041f\u0430\u043c\u044f\u0442\u044c',
  online_users:'\u041e\u043d\u043b\u0430\u0439\u043d \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438',sessions:'\u0441\u0435\u0441\u0441\u0438\u0439',
  recently_active:'\u041d\u0435\u0434\u0430\u0432\u043d\u043e \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0435 (1\u0447)',connection_log:'\u0416\u0443\u0440\u043d\u0430\u043b \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0439',
  no_conn_data:'\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445 \u043e \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f\u0445',
  top_destinations:'\u0422\u043e\u043f \u043d\u0430\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0439 (\u043f\u043e \u0434\u043e\u043c\u0435\u043d\u0430\u043c)',
  traffic_per_client:'\u0422\u0440\u0430\u0444\u0438\u043a \u043f\u043e \u043a\u043b\u0438\u0435\u043d\u0442\u0430\u043c',port_breakdown:'\u041f\u043e\u0440\u0442\u044b',
  unique_ips:'\u0423\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0445 IP',unique_ips_label:'\u0423\u043d\u0438\u043a. IP',user_connections:'\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439',no_client_data:'\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445',no_port_data:'\u041d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445',
  client_ip:'IP \u043a\u043b\u0438\u0435\u043d\u0442\u0430',agent:'\u0410\u0433\u0435\u043d\u0442',conn:'\u041f\u043e\u0434\u043a\u043b.',last_seen:'\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u044f\u044f \u0430\u043a\u0442.',
  port:'\u041f\u043e\u0440\u0442',svc_name:'\u0421\u0435\u0440\u0432\u0438\u0441',count:'\u041a\u043e\u043b-\u0432\u043e',destination:'\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435',
  time:'\u0412\u0440\u0435\u043c\u044f',ip:'IP',user_agent:'\u0410\u0433\u0435\u043d\u0442',event:'\u0421\u043e\u0431\u044b\u0442\u0438\u0435',
  sessions_active_no_ip:'\u0421\u0435\u0441\u0441\u0438\u0438 \u0430\u043a\u0442\u0438\u0432\u043d\u044b, \u043d\u043e \u043d\u0435\u0442 IP \u0438\u0437 \u043b\u043e\u0433\u043e\u0432',
  no_active_conn:'\u041d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0439',
  user:'\u043f\u043e\u043b\u044c\u0437.',users_pl:'\u043f\u043e\u043b\u044c\u0437.',add_user:'+ \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c',
  active_ip:'\u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0439 IP',active_ips:'\u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 IP',
  search_users:'\u041f\u043e\u0438\u0441\u043a \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439...',
  sort_name_az:'\u0418\u043c\u044f A\u2192Z',sort_name_za:'\u0418\u043c\u044f Z\u2192A',sort_date_new:'\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043d\u043e\u0432\u044b\u0435',sort_date_old:'\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0441\u0442\u0430\u0440\u044b\u0435',
  add_vpn_user:'\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c VPN \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f',username:'\u0418\u043c\u044f \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f',
  password:'\u041f\u0430\u0440\u043e\u043b\u044c',password_empty_auto:'\u041f\u0430\u0440\u043e\u043b\u044c (\u043f\u0443\u0441\u0442\u043e = \u0430\u0432\u0442\u043e)',
  create:'\u0421\u043e\u0437\u0434\u0430\u0442\u044c',cancel:'\u041e\u0442\u043c\u0435\u043d\u0430',close:'\u0417\u0430\u043a\u0440\u044b\u0442\u044c',copy:'\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c',copied:'\u0421\u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u043e!',
  config:'\u041a\u043e\u043d\u0444\u0438\u0433',
  delete_user:'\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f',delete_confirm:'\u0412\u044b \u0443\u0432\u0435\u0440\u0435\u043d\u044b, \u0447\u0442\u043e \u0445\u043e\u0442\u0438\u0442\u0435 \u0443\u0434\u0430\u043b\u0438\u0442\u044c',
  confirm:'\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c',
  change_password:'\u0421\u043c\u0435\u043d\u0438\u0442\u044c \u043f\u0430\u0440\u043e\u043b\u044c',new_password:'\u041d\u043e\u0432\u044b\u0439 \u043f\u0430\u0440\u043e\u043b\u044c',save:'\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c',
  renew_confirm:'\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442? \u0421\u0435\u0440\u0432\u0438\u0441 \u0431\u0443\u0434\u0435\u0442 \u043f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0449\u0435\u043d.',
  new_admin_password:'\u041d\u043e\u0432\u044b\u0439 \u043f\u0430\u0440\u043e\u043b\u044c \u0430\u0434\u043c\u0438\u043d\u0430 (6+ \u0441\u0438\u043c\u0432.)',
  read_only:'\u0442\u043e\u043b\u044c\u043a\u043e \u0447\u0442\u0435\u043d\u0438\u0435',
  service_logs:'\u041b\u043e\u0433\u0438 \u0441\u0435\u0440\u0432\u0438\u0441\u0430',click_refresh:'\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c \u0434\u043b\u044f \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438',
  initial_setup:'\u041d\u0430\u0447\u0430\u043b\u044c\u043d\u0430\u044f \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430',create_admin_pw:'\u0421\u043e\u0437\u0434\u0430\u0439\u0442\u0435 \u043f\u0430\u0440\u043e\u043b\u044c \u0430\u0434\u043c\u0438\u043d\u0430',
  enter_admin_pw:'\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043f\u0430\u0440\u043e\u043b\u044c \u0430\u0434\u043c\u0438\u043d\u0430',create_password:'\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043f\u0430\u0440\u043e\u043b\u044c',sign_in:'\u0412\u043e\u0439\u0442\u0438',
  loading:'\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430...',render_error:'\u041e\u0448\u0438\u0431\u043a\u0430 \u0440\u0435\u043d\u0434\u0435\u0440\u0430',
  apply_changes:'\u041f\u0440\u0438\u043c\u0435\u043d\u0438\u0442\u044c',pending_restart:'\u041a\u043e\u043d\u0444\u0438\u0433\u0443\u0440\u0430\u0446\u0438\u044f \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0430, \u0442\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f \u043f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u043a',
  password_btn:'\u041f\u0430\u0440\u043e\u043b\u044c',logout:'\u0412\u044b\u0445\u043e\u0434',
  changed_relogin:'\u041f\u0430\u0440\u043e\u043b\u044c \u0438\u0437\u043c\u0435\u043d\u0451\u043d, \u0432\u043e\u0439\u0434\u0438\u0442\u0435 \u0441\u043d\u043e\u0432\u0430',
  deleted:'\u0423\u0434\u0430\u043b\u0435\u043d\u043e',changed:'\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u043e',saved:'\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e',
  user_created:'\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0441\u043e\u0437\u0434\u0430\u043d',pass_label:'\u043f\u0430\u0440\u043e\u043b\u044c',
  qr_not_loaded:'QR \u0431\u0438\u0431\u043b\u0438\u043e\u0442\u0435\u043a\u0430 \u043d\u0435 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u0430',
  theme_dark:'\u0422\u0451\u043c\u043d\u0430\u044f',theme_light:'\u0421\u0432\u0435\u0442\u043b\u0430\u044f',theme_system:'\u0421\u0438\u0441\u0442\u0435\u043c\u0430',
  s_ago:'\u0441 \u043d\u0430\u0437\u0430\u0434',m_ago:'\u043c \u043d\u0430\u0437\u0430\u0434',h_ago:'\u0447 \u043d\u0430\u0437\u0430\u0434',d_ago:'\u0434 \u043d\u0430\u0437\u0430\u0434',
  ip_address:'IP \u0430\u0434\u0440\u0435\u0441',location:'\u041b\u043e\u043a\u0430\u0446\u0438\u044f',isp:'\u041f\u0440\u043e\u0432\u0430\u0439\u0434\u0435\u0440',destinations:'\u041d\u0430\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u044f',
  svc_action_ok:'OK',no_cert:'\u041d\u0435\u0442 \u0441\u0435\u0440\u0442.',auto_renew:'\u0410\u0432\u0442\u043e-\u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u0432\u043a\u043b.',
  change:'\u0421\u043c\u0435\u043d\u0438\u0442\u044c',config_for:'\u041a\u043e\u043d\u0444\u0438\u0433',
  btn_config:'\u041a\u043e\u043d\u0444\u0438\u0433',btn_qr:'QR',btn_pass:'\u041f\u0430\u0440\u043e\u043b\u044c',btn_del:'\u0423\u0434\u0430\u043b\u0438\u0442\u044c',
  btn_enable:'\u0412\u043a\u043b\u044e\u0447\u0438\u0442\u044c',btn_disable:'\u041e\u0442\u043a\u043b\u044e\u0447\u0438\u0442\u044c',created_label:'\u0421\u043e\u0437\u0434\u0430\u043d',
  user_enabled:'\u0412\u043a\u043b\u044e\u0447\u0435\u043d',user_disabled:'\u041e\u0442\u043a\u043b\u044e\u0447\u0435\u043d',
  show_more:'\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u0435\u0449\u0451',show_less:'\u0421\u0432\u0435\u0440\u043d\u0443\u0442\u044c',of_total:'\u0438\u0437',
  prev_page:'\u041d\u0430\u0437\u0430\u0434',next_page:'\u0412\u043f\u0435\u0440\u0451\u0434'
}};
function t(k){return (T[S.lang]||T.en)[k]||T.en[k]||k}
function setLang(l){S.lang=l;localStorage.setItem('tt_lang',l);R()}
function setTheme(th){S.theme=th;localStorage.setItem('tt_theme',th);applyTheme()}
function applyTheme(){document.documentElement.setAttribute('data-theme',S.theme)}
var S={auth:false,setup:false,loading:true,tab:'dashboard',status:null,users:[],logs:null,settings:{},
  history:null,traffic:null,conns:null,online:null,summary:null,toast:null,modal:null,dbSize:null,
  connTimeline:null,activeIps:{},monPeriod:24,connPeriod:24,pendingReload:false,userFilter:'',userSort:'name_asc',monLoading:false,logsLoading:false,
  lang:localStorage.getItem('tt_lang')||'en',theme:localStorage.getItem('tt_theme')||'system'};

// ─── API ────────────────────────────────────────────────
async function api(p,o){o=o||{};var r=await fetch(A+p,{headers:{'Content-Type':'application/json'},credentials:'same-origin',...o});var d=await r.json();if(!r.ok)throw new Error(d.detail||r.statusText);return d}
function toast(m,e){S.toast={m:m,e:!!e};R();setTimeout(function(){S.toast=null;R()},3500)}
function fmt(b){if(b==null)return '0 B';if(b>=1099511627776)return(b/1099511627776).toFixed(2)+' TB';if(b>=1073741824)return(b/1073741824).toFixed(2)+' GB';if(b>=1048576)return(b/1048576).toFixed(1)+' MB';if(b>=1024)return(b/1024).toFixed(0)+' KB';return b+' B'}
function fmtShort(b){if(b==null)return '0';if(b>=1099511627776)return(b/1099511627776).toFixed(1)+' TB';if(b>=1073741824)return(b/1073741824).toFixed(1)+' GB';if(b>=1048576)return(b/1048576).toFixed(0)+' MB';if(b>=1024)return(b/1024).toFixed(0)+' KB';return b+' B'}
function fmtTooltip(b){if(b==null)return '0 B';if(b>=1099511627776)return(b/1099511627776).toFixed(2)+' TB';if(b>=1073741824)return(b/1073741824).toFixed(2)+' GB';if(b>=1048576)return(b/1048576).toFixed(1)+' MB';if(b>=1024)return(b/1024).toFixed(0)+' KB';return b+' B'}
function ts2t(ts){var d=new Date(ts*1000);var hh=String(d.getHours()).padStart(2,'0')+':00';if(d.getHours()===0)return d.getDate()+'.'+(d.getMonth()+1)+' '+hh;return hh}
function ts2h(ts){return ts2t(ts)}
function ts2dt(ts){return new Date(ts*1000).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
function ago(ts){var d=Math.floor(Date.now()/1000-ts);if(d<60)return d+' '+t('s_ago');if(d<3600)return Math.floor(d/60)+' '+t('m_ago');if(d<86400)return Math.floor(d/3600)+' '+t('h_ago');return Math.floor(d/86400)+' '+t('d_ago')}
function fmtUptime(sec){if(!sec)return '\u2014';var d=Math.floor(sec/86400),h=Math.floor((sec%86400)/3600),m=Math.floor((sec%3600)/60);if(d>0)return d+'d '+h+'h '+m+'m';if(h>0)return h+'h '+m+'m';return m+'m'}

// (#15) Loading state helper
function withLoading(btn,fn){
  if(!btn)return fn();
  var orig=btn.textContent;btn.disabled=true;btn.textContent='...';
  return Promise.resolve(fn()).finally(function(){if(btn.parentNode){btn.disabled=false;btn.textContent=orig}})}

// ─── Auth ───────────────────────────────────────────────
async function checkAuth(){try{var r=await api('/auth-status');S.auth=r.authenticated;S.setup=r.setup_required}catch(e){S.auth=false}S.loading=false;R()}
async function doLogin(pw){try{await api('/login',{method:'POST',body:JSON.stringify({password:pw})});S.auth=true;loadAll()}catch(e){toast(e.message,true)}R()}
async function doSetup(pw){try{await api('/setup',{method:'POST',body:JSON.stringify({password:pw})});S.setup=false;await doLogin(pw)}catch(e){toast(e.message,true)}}
async function doLogout(){await api('/logout',{method:'POST'});S.auth=false;R()}

// ─── Data loaders ───────────────────────────────────────
async function loadAll(){
  await Promise.all([_loadDash(),_loadSummary(),_checkPendingReload()]);
  R()
}
async function loadDash(){await _loadDash();R()}
async function _loadDash(){try{var p=await Promise.all([api('/status'),api('/users')]);S.status=p[0];S.users=p[1].users}catch(e){toast(e.message,true)}await _loadActiveIps()}
async function _loadSummary(){try{S.summary=await api('/monitoring/summary')}catch(e){}}
async function _loadHistory(h){if(h!=null)S.monPeriod=h;try{S.history=await api('/monitoring/history?hours='+S.monPeriod)}catch(e){toast(e.message,true)}}
async function _loadConns(h){if(h!=null)S.connPeriod=h;try{S.conns=await api('/monitoring/connections?hours='+S.connPeriod)}catch(e){toast(e.message,true)}}
async function _loadConnTimeline(){try{S.connTimeline=await api('/monitoring/conn-timeline?hours='+S.monPeriod)}catch(e){}}
async function _loadOnline(){try{S.online=await api('/monitoring/online')}catch(e){}}
async function _loadDbSize(){try{S.dbSize=await api('/monitoring/db-size')}catch(e){}}
async function _loadActiveIps(){try{var r=await api('/active-ips');S.activeIps=r.active_ips||{}}catch(e){}}
async function _checkPendingReload(){try{var r=await api('/pending-reload');S.pendingReload=r.pending}catch(e){}}
async function loadHistory(h){await Promise.all([_loadHistory(h),_loadTraffic(),_loadConnTimeline()]);R(drawMonitorCharts)}
async function _loadTraffic(d){try{var url=S.tab==='monitor'?'/monitoring/traffic?hours='+S.monPeriod:'/monitoring/traffic?days='+(d||7);S.traffic=await api(url)}catch(e){}}
async function loadTraffic(d){await _loadTraffic(d);R(drawTrafficChart)}
async function loadConns(h){await _loadConns(h);R()}
async function loadOnline(){await _loadOnline();R()}
async function loadLogs(){S.logsLoading=true;R();try{var r=await api('/logs?lines=200');S.logs=r.logs||'(empty log file)'}catch(e){S.logs='Error: '+e.message;toast(e.message,true)}S.logsLoading=false;R()}
async function loadSettings(){try{S.settings=await api('/settings')}catch(e){toast(e.message,true)}R()}
async function loadMonitorAll(){
  S.monLoading=true;R();
  await Promise.all([_loadHistory(),_loadTraffic(),_loadConnTimeline(),_loadOnline(),_loadConns(),_loadDbSize()]);
  S.monLoading=false;R(drawMonitorCharts)
}
function drawMonitorCharts(){if(!window.Chart){setTimeout(drawMonitorCharts,200);return}drawAllCharts();drawTrafficChart();drawConnChart()}

// ─── User actions (#14 modal dialogs, #15 loading) ──────
async function toggleUser(u,btn){await withLoading(btn,async function(){try{var r=await api('/users/'+u+'/toggle',{method:'PUT'});var user=S.users.find(function(x){return x.username===u});if(user)user.enabled=r.enabled;toast(r.enabled?t('user_enabled'):t('user_disabled'));R()}catch(e){toast(e.message,true)}})}
function copyPassword(pw){navigator.clipboard.writeText(pw).then(function(){toast(t('copied'))}).catch(function(){toast('Copy failed',true)})}
async function addUser(u,p){try{var r=await api('/users',{method:'POST',body:JSON.stringify({username:u,password:p})});toast(t('user_created')+' "'+u+'" ('+t('pass_label')+': '+r.password+')');S.modal=null;loadDash()}catch(e){toast(e.message,true)}}
async function deleteUser(u){S.modal={t:'confirm',title:t('delete_user'),msg:t('delete_confirm')+' "'+u+'"?',onConfirm:async function(btn){await withLoading(btn,async function(){try{await api('/users/'+u,{method:'DELETE'});toast(t('deleted'));S.modal=null;loadDash()}catch(e){toast(e.message,true)}})}};R()}
async function chgPass(u){S.modal={t:'chgpass',u:u};R()}
async function doChgPass(u,p,btn){if(!p){toast(t('password')+' required',true);return}await withLoading(btn,async function(){try{await api('/users/'+u,{method:'PUT',body:JSON.stringify({password:p})});toast(t('changed'));S.modal=null;loadDash()}catch(e){toast(e.message,true)}})}
async function showCfg(u,f){try{var r=await api('/users/'+u+'/config?fmt='+f);S.modal={t:'cfg',u:u,c:r.config,f:f};R();if(f==='deeplink')setTimeout(function(){var el=document.getElementById('qr-t');if(el&&window.QRCode){el.innerHTML='';new QRCode(el,{text:r.config,width:200,height:200,correctLevel:QRCode.CorrectLevel.M})}else if(el){el.textContent=t('qr_not_loaded')}},100)}catch(e){toast(e.message,true)}}
async function svcAct(a,btn){await withLoading(btn,async function(){try{await api('/service/'+a,{method:'POST'});toast(t('service')+' '+a+' '+t('svc_action_ok'));setTimeout(loadDash,2000)}catch(e){toast(e.message,true)}})}
async function saveCfg(f,c){try{await api('/settings/'+f,{method:'PUT',body:JSON.stringify({content:c})});toast(t('saved'))}catch(e){toast(e.message,true)}}
async function renewCert(){S.modal={t:'confirm',title:t('renew_cert'),msg:t('renew_confirm'),onConfirm:async function(btn){if(btn){btn.disabled=true;btn.textContent='...'}try{var r=await api('/cert/renew',{method:'POST'});S.modal=null;toast(r.message,!r.ok);setTimeout(loadAll,3000)}catch(e){S.modal=null;toast(e.message,true)}}};R()}
async function chgAdmin(){S.modal={t:'chgadmin'};R()}
async function doChgAdmin(p,btn){if(!p||p.length<6){toast('Min 6 chars',true);return}await withLoading(btn,async function(){try{await api('/change-password',{method:'POST',body:JSON.stringify({password:p})});toast(t('changed_relogin'));S.auth=false;S.modal=null;R()}catch(e){toast(e.message,true)}})}
// (#17) Apply pending reload
async function applyReload(btn){await withLoading(btn,async function(){try{await api('/apply-reload',{method:'POST'});toast(t('service')+' '+t('restart').toLowerCase());S.pendingReload=false;R();setTimeout(loadDash,2000)}catch(e){toast(e.message,true)}})}

// ─── Charts (#8 update instead of destroy/recreate) ─────
var charts={};
var chartColors={
  sessions:{border:'#3b9eff',bg:'rgba(59,158,255,0.08)'},
  download:{border:'#22c55e',bg:'rgba(34,197,94,0.08)'},
  upload:{border:'#f59e0b',bg:'rgba(245,158,11,0.08)'},
  memory:{border:'#a78bfa',bg:'rgba(167,139,250,0.08)'},
  cpu:{border:'#06b6d4',bg:'rgba(6,182,212,0.08)'}
};
var chartOpts=function(yCallback){return{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:false},tooltip:{backgroundColor:'#131a24',borderColor:'#1e2a3a',borderWidth:1,titleColor:'#e2e8f0',bodyColor:'#8899aa',titleFont:{family:'DM Sans',size:12,weight:600},bodyFont:{family:'JetBrains Mono',size:11},padding:10,cornerRadius:8,displayColors:true,boxWidth:8,boxHeight:8,boxPadding:4}},scales:{x:{display:true,ticks:{color:'#556677',font:{family:'JetBrains Mono',size:9},maxTicksLimit:8,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,ticks:{color:'#556677',font:{family:'JetBrains Mono',size:9},callback:yCallback||undefined,maxTicksLimit:5},grid:{color:'rgba(30,42,58,0.5)',drawBorder:false},border:{display:false}}}}};
var mkDataset=function(label,data,color,fill){return{label:label,data:data,borderColor:color.border,backgroundColor:color.bg,fill:fill!==false,tension:.35,pointRadius:0,pointHoverRadius:4,borderWidth:1.5}};

function updateChart(key,canvas,cfg){
  if(!canvas)return;
  // Check if old chart still points to a valid (attached) canvas
  if(charts[key]){
    if(charts[key].canvas&&charts[key].canvas.isConnected){
      // Canvas still in DOM — update in place (no flicker)
      var ch=charts[key];
      ch.data.labels=cfg.data.labels;
      for(var i=0;i<cfg.data.datasets.length;i++){
        if(ch.data.datasets[i]){ch.data.datasets[i].data=cfg.data.datasets[i].data}
        else{ch.data.datasets.push(cfg.data.datasets[i])}
      }
      while(ch.data.datasets.length>cfg.data.datasets.length)ch.data.datasets.pop();
      ch.update('none');
      return;
    }
    // Canvas was removed from DOM — destroy old instance
    try{charts[key].destroy()}catch(x){}
  }
  charts[key]=new Chart(canvas,cfg);
}

function drawAllCharts(){
  if(!window.Chart){setTimeout(drawAllCharts,500);return}
  if(!S.history||!S.history.snapshots.length)return;
  var d=S.history.snapshots;
  var labels=d.map(function(x){return ts2t(x.ts)});

  var c1=document.getElementById('ch-sessions');
  if(c1){updateChart('sess',c1,{type:'line',data:{labels:labels,datasets:[mkDataset('Sessions',d.map(function(x){return x.sessions}),chartColors.sessions)]},options:chartOpts()})}


  var c3=document.getElementById('ch-resources');
  if(c3){
    var cpuPct=d.map(function(x,i){if(i===0)return 0;var dt=x.ts-d[i-1].ts;if(dt<=0)return 0;return Math.min(100,((x.cpu-d[i-1].cpu)/dt)*100)});
    updateChart('res',c3,{type:'line',data:{labels:labels,datasets:[
      {label:'Memory MB',data:d.map(function(x){return x.mem/1048576}),borderColor:chartColors.memory.border,backgroundColor:chartColors.memory.bg,fill:true,tension:.35,pointRadius:0,borderWidth:1.5,yAxisID:'y'},
      {label:'CPU %',data:cpuPct,borderColor:chartColors.cpu.border,backgroundColor:'transparent',fill:false,tension:.35,pointRadius:0,borderWidth:1.5,yAxisID:'y1'}
    ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,labels:{color:'#8899aa',font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:'#131a24',borderColor:'#1e2a3a',borderWidth:1,titleColor:'#e2e8f0',bodyColor:'#8899aa',padding:10,cornerRadius:8}},scales:{x:{display:true,ticks:{color:'#556677',font:{family:'JetBrains Mono',size:9},maxTicksLimit:8,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,position:'left',title:{display:true,text:'Memory MB',color:'#556677',font:{size:9}},ticks:{color:'#556677',font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{color:'rgba(30,42,58,0.5)'},border:{display:false}},y1:{display:true,position:'right',title:{display:true,text:'CPU %',color:'#556677',font:{size:9}},ticks:{color:'#556677',font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{display:false},border:{display:false},min:0}}}})}
}

function drawTrafficChart(){
  if(!window.Chart){setTimeout(drawTrafficChart,500);return}
  if(!S.traffic||!S.traffic.hourly.length)return;
  var d=S.traffic.hourly;var c=document.getElementById('ch-traffic');
  if(c){
    var labels=d.map(function(x){return ts2t(x.ts)});
    updateChart('traffic',c,{type:'bar',data:{labels:labels,datasets:[{label:'Download',data:d.map(function(x){return x.out}),backgroundColor:'rgba(34,197,94,0.5)',borderRadius:3},{label:'Upload',data:d.map(function(x){return x['in']}),backgroundColor:'rgba(245,158,11,0.5)',borderRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,labels:{color:'#8899aa',font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:'#131a24',borderColor:'#1e2a3a',borderWidth:1,titleColor:'#e2e8f0',bodyColor:'#8899aa',padding:10,cornerRadius:8,callbacks:{label:function(ctx){return ctx.dataset.label+': '+fmtTooltip(ctx.raw)}}}},scales:{x:{display:true,ticks:{color:'#556677',font:{family:'JetBrains Mono',size:8},maxTicksLimit:24,maxRotation:0},stacked:true,grid:{display:false},border:{display:false}},y:{display:true,ticks:{color:'#556677',font:{family:'JetBrains Mono',size:9},callback:function(v){return fmtShort(v)},maxTicksLimit:5},grid:{color:'rgba(30,42,58,0.5)'},stacked:true,border:{display:false}}}}})
  }
}

function drawConnChart(){
  if(!window.Chart)return;
  if(!S.connTimeline||!S.connTimeline.timeline.length)return;
  var d=S.connTimeline.timeline;var c=document.getElementById('ch-conns');
  if(c){
    var connColor={border:'#a78bfa',bg:'rgba(167,139,250,0.3)'};
    var ipColor={border:'#06b6d4',bg:'rgba(6,182,212,0.3)'};
    var opts=chartOpts();opts.plugins={...opts.plugins,legend:{display:true,labels:{color:'#8899aa',font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}}};
    updateChart('conns',c,{type:'bar',data:{
      labels:d.map(function(x){return ts2t(x.ts)}),
      datasets:[
        {label:t('connections'),data:d.map(function(x){return x.connections}),backgroundColor:connColor.bg,borderColor:connColor.border,borderWidth:1,borderRadius:3,order:2},
        {label:t('unique_ips_label'),data:d.map(function(x){return x.unique_ips}),type:'line',borderColor:ipColor.border,backgroundColor:'transparent',borderWidth:2,tension:.35,pointRadius:2,pointBackgroundColor:ipColor.border,order:1,yAxisID:'y1'}
      ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:opts.plugins,scales:{x:{display:true,ticks:{color:'#556677',font:{family:'JetBrains Mono',size:9},maxTicksLimit:8,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,position:'left',title:{display:true,text:t('connections'),color:'#556677',font:{size:9}},ticks:{color:'#556677',font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{color:'rgba(30,42,58,0.5)'},border:{display:false}},y1:{display:true,position:'right',title:{display:true,text:t('unique_ips_label'),color:'#556677',font:{size:9}},ticks:{color:'#556677',font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{display:false},border:{display:false},min:0}}}})
  }
}

// ─── DOM helper ─────────────────────────────────────────
function h(t,a){var e=document.createElement(t);var deferValue=null;if(a){var keys=Object.keys(a);for(var ki=0;ki<keys.length;ki++){var k=keys[ki],v=a[k];if(k==='style'&&typeof v==='object')Object.assign(e.style,v);else if(k.substr(0,2)==='on')e.addEventListener(k.slice(2).toLowerCase(),v);else if(k==='className')e.className=v;else if(k==='innerHTML')e.innerHTML=v;else if(k==='value'){deferValue=v}else if(k==='checked'||k==='selected'||k==='disabled'){if(v!==false&&v!=null)e[k]=v}else e.setAttribute(k,v)}}for(var i=2;i<arguments.length;i++){var x=arguments[i];if(Array.isArray(x)){for(var j=0;j<x.length;j++)appendNode(e,x[j])}else{appendNode(e,x)}}if(deferValue!==null)e.value=deferValue;return e}
function appendNode(e,x){if(x==null||x===false||x===undefined)return;if(typeof x==='number')x=String(x);if(typeof x==='string')e.appendChild(document.createTextNode(x));else if(x.nodeType)e.appendChild(x);else if(Array.isArray(x)){for(var i=0;i<x.length;i++)appendNode(e,x[i])}}

function loadingView(full){return h('div',{className:'loading-box',style:full?{minHeight:'60vh'}:{}},h('div',{className:'spinner'+(full?' spinner-lg':'')}),t('loading'))}

// ─── Period selector component ──────────────────────────
function periodSelector(current,periods,onChange){
  var btns=[];for(var i=0;i<periods.length;i++){(function(p){btns.push(h('button',{className:'per'+(current===p.v?' on':''),onClick:function(){onChange(p.v)}},p.l))})(periods[i])}
  return h('div',{className:'periods'},btns)}

// ─── Pagination component ────────────────────────────────
var _pageState={};
function paginatedList(key,items,renderFn,pageSize){
  pageSize=pageSize||20;if(!items||!items.length)return null;
  if(!_pageState[key])_pageState[key]=0;
  var page=_pageState[key];var total=items.length;var pages=Math.ceil(total/pageSize);
  if(page>=pages)page=pages-1;if(page<0)page=0;_pageState[key]=page;
  var start=page*pageSize;var slice=items.slice(start,start+pageSize);
  var content=slice.map(renderFn);
  if(pages<=1)return h('div',null,content);
  return h('div',null,content,
    h('div',{style:{display:'flex',justifyContent:'center',alignItems:'center',gap:'10px',padding:'10px 0',fontSize:'11px',color:'var(--tx2)'}},
      h('button',{className:'btn btn-xs',disabled:page===0,onClick:function(){_pageState[key]=page-1;R()}},'\u25C0'),
      (start+1)+'\u2013'+Math.min(start+pageSize,total)+' '+t('of_total')+' '+total,
      h('button',{className:'btn btn-xs',disabled:page>=pages-1,onClick:function(){_pageState[key]=page+1;R()}},'\u25B6')))
}

// ─── Expandable card ─────────────────────────────────────
var _expandState={};
function expandableCard(key,title,content,extraStyle){
  var open=!!_expandState[key];
  var wrap=h('div',{style:open?{}:{maxHeight:'220px',overflow:'hidden',position:'relative'}},content);
  if(!open){wrap.appendChild(h('div',{style:{position:'absolute',bottom:0,left:0,right:0,height:'60px',background:'linear-gradient(transparent,var(--sf))',pointerEvents:'none'}}))}
  return h('div',{className:'card',style:extraStyle||{}},
    h('div',{className:'card-t'},h('span',null,title)),
    wrap,
    h('div',{style:{textAlign:'center',paddingTop:'6px'}},
      h('button',{className:'btn btn-xs',style:{fontSize:'10px'},onClick:function(){_expandState[key]=!open;R()}},
        open?t('show_less'):t('show_more'))))
}

// ─── Render ─────────────────────────────────────────────
var _rTimer=null;var _rCallbacks=[];
function R(cb){if(cb)_rCallbacks.push(cb);if(_rTimer)return;_rTimer=requestAnimationFrame(function(){_rTimer=null;_doRender();var cbs=_rCallbacks.slice();_rCallbacks=[];for(var i=0;i<cbs.length;i++)cbs[i]()})}
function _doRender(){
  var root=document.getElementById('root');
  try{
  root.innerHTML='';
  if(S.toast)root.appendChild(h('div',{className:'toast '+(S.toast.e?'toast-err':'toast-ok')},S.toast.m));
  if(S.modal)root.appendChild(renderModal());
  if(S.loading)return root.appendChild(loadingView(true));
  if(!S.auth)return root.appendChild(renderLogin());
  root.appendChild(renderApp());
  }catch(err){var msg=String(err.message||err).replace(/\x3c/g,'&lt;');root.innerHTML='\x3cdiv style="color:#ef4444;padding:40px;font-family:monospace;font-size:13px"\x3e\x3cb\x3eRender error:\x3c/b\x3e\x3cbr\x3e\x3cpre\x3e'+msg+'\x3c/pre\x3e\x3c/div\x3e';console.error('R() error:',err)}
}

function renderLogin(){
  var pw;var isS=S.setup;
  var card=h('div',{className:'lw'},h('div',{className:'lc'},
    h('div',{style:{textAlign:'center',marginBottom:'20px'}},h('img',{src:LOGO_FULL,className:'logo-img',style:{maxHeight:'56px',maxWidth:'260px',width:'auto',height:'auto',margin:'0 auto 12px'}})),
    h('div',{className:'lt'},isS?t('initial_setup'):''),
    h('div',{className:'ls'},isS?t('create_admin_pw'):t('enter_admin_pw')),
    h('div',{className:'fg'},pw=h('input',{className:'input',type:'password',placeholder:t('password'),style:{textAlign:'center'}})),
    h('button',{className:'btn btn-p',style:{width:'100%',justifyContent:'center',padding:'12px',fontSize:'13px',borderRadius:'10px'},onClick:function(){isS?doSetup(pw.value):doLogin(pw.value)}},isS?t('create_password'):t('sign_in')),
    h('div',{style:{display:'flex',justifyContent:'center',marginTop:'16px',gap:'8px'}},
      h('div',{className:'lg'},
        h('button',{className:S.lang==='en'?'on':'',onClick:function(){setLang('en')}},'EN'),
        h('button',{className:S.lang==='ru'?'on':'',onClick:function(){setLang('ru')}},'\u0420\u0423')),
      h('div',{className:'tg'},
        h('button',{className:S.theme==='dark'?'on':'',onClick:function(){setTheme('dark')},title:t('theme_dark')},'\u263E'),
        h('button',{className:S.theme==='light'?'on':'',onClick:function(){setTheme('light')},title:t('theme_light')},'\u2600'),
        h('button',{className:S.theme==='system'?'on':'',onClick:function(){setTheme('system')},title:t('theme_system')},'\u2699')))));
  setTimeout(function(){if(pw){pw.addEventListener('keydown',function(e){if(e.key==='Enter')(isS?doSetup:doLogin)(pw.value)});pw.focus()}},50);
  return card;
}

function renderApp(){
  var tabs=[
    {id:'dashboard',label:t('dashboard')},
    {id:'monitor',label:t('monitor')},
    {id:'users',label:t('users')},
    {id:'settings',label:t('settings')},
    {id:'logs',label:t('logs')}
  ];
  return h('div',{className:'app fade-in'},
    h('div',{className:'hdr'},
      h('div',{className:'logo'},
        h('img',{src:LOGO_FULL,className:'logo-img',style:{height:'34px',width:'auto'}}),
        h('div',{className:'logo-s',style:{marginLeft:'8px'}},(S.status&&S.status.domain)||'')),
      h('div',{className:'bg'},
        h('div',{className:'lg'},
          h('button',{className:S.lang==='en'?'on':'',onClick:function(){setLang('en')}},'EN'),
          h('button',{className:S.lang==='ru'?'on':'',onClick:function(){setLang('ru')}},'\u0420\u0423')),
        h('div',{className:'tg'},
          h('button',{className:S.theme==='dark'?'on':'',onClick:function(){setTheme('dark')},title:t('theme_dark')},'\u263E'),
          h('button',{className:S.theme==='light'?'on':'',onClick:function(){setTheme('light')},title:t('theme_light')},'\u2600'),
          h('button',{className:S.theme==='system'?'on':'',onClick:function(){setTheme('system')},title:t('theme_system')},'\u2699')),
        h('button',{className:'btn btn-xs btn-ghost',onClick:chgAdmin},t('password_btn')),
        h('button',{className:'btn btn-xs btn-ghost',onClick:doLogout},t('logout')))),
    S.pendingReload?h('div',{className:'apply-bar'},
      h('span',null,t('pending_restart')),
      h('button',{className:'btn btn-sm',style:{background:'var(--or2)',borderColor:'var(--or)'},onClick:function(e){applyReload(e.currentTarget)}},t('apply_changes'))):null,
    h('div',{className:'tabs'},tabs.map(function(tb){return h('button',{className:'tab'+(S.tab===tb.id?' on':''),
      onClick:function(){S.tab=tb.id;if(tb.id==='monitor')loadMonitorAll();if(tb.id==='logs')loadLogs();if(tb.id==='settings')loadSettings();if(tb.id==='dashboard')loadAll();if(tb.id==='users')loadDash();R()}},
      tb.label)})),
    S.tab==='dashboard'?renderDash():S.tab==='monitor'?renderMonitor():S.tab==='users'?renderUsers():S.tab==='settings'?renderSettings():renderLogs()
  );
}

// ─── Dashboard ──────────────────────────────────────────
function mkVpsStat(label,pct,unit,color,sub){
  var barColor='var('+color+')';
  return h('div',{className:'stat'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'baseline'}},
      h('div',{className:'stat-l'},label),
      h('div',{style:{fontSize:'16px',fontWeight:'700',fontFamily:'var(--m)',color:barColor}},String(pct)+unit)),
    h('div',{style:{height:'6px',background:'var(--sf3)',borderRadius:'3px',marginTop:'8px',overflow:'hidden'}},
      h('div',{style:{width:pct+'%',height:'100%',background:barColor,borderRadius:'3px',transition:'width .5s'}})),
    sub?h('div',{className:'stat-sub',style:{marginTop:'4px'}},sub):null)
}

function renderDash(){
  var s=S.status;if(!s){loadAll();return loadingView()}
  var l=s.live||{};var cert=s.certificate;var sm=S.summary;
  var certDays=cert?cert.days:null;var certClass=certDays!=null?(certDays<14?'off':certDays<30?'warn':'on'):'';

  return h('div',{className:'fade-in'},
    h('div',{className:'grid grid4 section-gap'},
      h('div',{className:'stat '+(s.service&&s.service.active?'stat-green':'stat-red')},
        h('div',{className:'stat-l'},t('service')),
        h('div',{className:'stat-v '+(s.service&&s.service.active?'on':'off')},s.service&&s.service.active?t('online'):t('offline')),
        s.service&&s.service.active?h('div',{className:'stat-sub'},h('span',{className:'dot dot-on pulse'}),t('running')):null),
      h('div',{className:'stat stat-cyan'},
        h('div',{className:'stat-l'},t('tcp_sessions')),
        h('div',{className:'stat-v ac'},String(l.sessions||0)),
        h('div',{className:'stat-sub'},String(s.users_count||0)+' '+t('users_configured'))),
      h('div',{className:'stat'},
        h('div',{className:'stat-l'},t('mem_cpu')),
        h('div',{className:'stat-v'},(l.memory_mb||0)+' MB'),
        h('div',{className:'stat-sub'},'CPU: '+(l.cpu_seconds||0)+'s total')),
      h('div',{className:'stat '+(certDays!=null&&certDays<14?'stat-red':certDays!=null&&certDays<30?'stat-orange':'')},
        h('div',{className:'stat-l'},t('certificate')),
        h('div',{className:'stat-v '+certClass},certDays!=null?certDays+'d':'\u2014'),
        h('div',{className:'stat-sub'},cert&&cert.date?cert.date:t('no_cert')),
        certDays!=null&&certDays<=10?h('div',{style:{fontSize:'9px',color:'var(--or)',marginTop:'2px'}},t('auto_renew')):null)
    ),

    s.vps?h('div',{className:'grid grid3 section-gap'},
      mkVpsStat('CPU',s.vps.cpu_pct,'%',s.vps.cpu_pct>80?'--rd':s.vps.cpu_pct>50?'--or':'--gn'),
      mkVpsStat('RAM',s.vps.ram_pct,'%',s.vps.ram_pct>80?'--rd':s.vps.ram_pct>50?'--or':'--gn',s.vps.ram_used_mb+'/'+s.vps.ram_total_mb+' MB'),
      mkVpsStat(t('disk'),s.vps.disk_pct,'%',s.vps.disk_pct>85?'--rd':s.vps.disk_pct>60?'--or':'--gn',s.vps.disk_used_gb+'/'+s.vps.disk_total_gb+' GB')
    ):null,

    sm?h('div',{className:'grid grid2 section-gap'},
      h('div',{className:'card',style:{margin:'0'}},
        h('div',{className:'card-t'},t('today')),
        h('div',{className:'grid grid2'},
          h('div',null,h('div',{className:'stat-l'},t('download')),h('div',{style:{fontSize:'16px',fontWeight:'700',fontFamily:'var(--m)',color:'var(--gn)'}},fmt(sm.today?sm.today.outbound:0))),
          h('div',null,h('div',{className:'stat-l'},t('upload')),h('div',{style:{fontSize:'16px',fontWeight:'700',fontFamily:'var(--m)',color:'var(--or)'}},fmt(sm.today?sm.today.inbound:0))),
          h('div',null,h('div',{className:'stat-l'},t('peak_sessions')),h('div',{style:{fontSize:'14px',fontWeight:'600',fontFamily:'var(--m)'}},String(sm.today?sm.today.peak_sessions:0))),
          h('div',null,h('div',{className:'stat-l'},t('connections')),h('div',{style:{fontSize:'14px',fontWeight:'600',fontFamily:'var(--m)'}},String(sm.today?sm.today.connections:0))))),
      h('div',{className:'card',style:{margin:'0'}},
        h('div',{className:'card-t'},t('this_week')),
        h('div',{className:'grid grid2'},
          h('div',null,h('div',{className:'stat-l'},t('download')),h('div',{style:{fontSize:'16px',fontWeight:'700',fontFamily:'var(--m)',color:'var(--gn)'}},fmt(sm.week?sm.week.outbound:0))),
          h('div',null,h('div',{className:'stat-l'},t('upload')),h('div',{style:{fontSize:'16px',fontWeight:'700',fontFamily:'var(--m)',color:'var(--or)'}},fmt(sm.week?sm.week.inbound:0))),
          h('div',null,h('div',{className:'stat-l'},t('peak_sessions')),h('div',{style:{fontSize:'14px',fontWeight:'600',fontFamily:'var(--m)'}},String(sm.week?sm.week.peak_sessions:0))),
          h('div',null,h('div',{className:'stat-l'},t('connections')),h('div',{style:{fontSize:'14px',fontWeight:'600',fontFamily:'var(--m)'}},String(sm.week?sm.week.connections:0)))))
    ):null,

    h('div',{className:'grid grid3 section-gap'},
      h('div',{className:'stat'},h('div',{className:'stat-l'},t('dl_restart')),h('div',{className:'stat-v',style:{color:'var(--gn)'}},fmt(l.outbound_bytes||0))),
      h('div',{className:'stat'},h('div',{className:'stat-l'},t('ul_restart')),h('div',{className:'stat-v',style:{color:'var(--or)'}},fmt(l.inbound_bytes||0))),
      h('div',{className:'stat'},h('div',{className:'stat-l'},t('sockets')),h('div',{className:'stat-v'},(l.tcp_sockets||0)+'/'+(l.udp_sockets||0)),h('div',{className:'stat-sub'},'FDs: '+(l.open_fds||0)))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('controls')),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-sm',onClick:function(e){svcAct('restart',e.currentTarget)}},t('restart')),
        h('button',{className:'btn btn-sm',onClick:function(e){svcAct('reload',e.currentTarget)}},t('reload_tls')),
        h('button',{className:'btn btn-sm btn-d',onClick:function(e){svcAct('stop',e.currentTarget)}},t('stop')),
        h('button',{className:'btn btn-sm',onClick:renewCert},t('renew_cert')))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('server_info')),
      h('div',{style:{fontFamily:'var(--m)',fontSize:'11px',color:'var(--tx3)',lineHeight:'1.8',whiteSpace:'pre-wrap'}},
        t('domain')+':          '+s.domain+'\nIP:              '+s.ip+'\nPID:             '+(s.service&&s.service.pid?s.service.pid:'\u2014')+'\n'+t('server_uptime')+':  '+fmtUptime(s.vps&&s.vps.uptime_seconds)+'\n'+t('service_uptime')+': '+fmtUptime(s.service&&s.service.uptime_seconds)))
  );
}

// ─── Monitor ────────────────────────────────────────────
function renderMonitor(){
  var periods=[{v:1,l:'1h'},{v:6,l:'6h'},{v:24,l:'24h'},{v:168,l:'7d'}];

  if(S.monLoading&&!S.history){return h('div',{className:'fade-in'},loadingView())}

  return h('div',{className:'fade-in'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'14px'}},
      h('div',{style:{fontSize:'12px',fontWeight:'600',color:'var(--tx2)'}},t('monitoring')),
      periodSelector(S.monPeriod,periods,function(v){loadHistory(v)})),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('active_sessions')),
      h('div',{className:'chart-wrap'},h('canvas',{id:'ch-sessions'}))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('traffic_hourly')),
      h('div',{className:'chart-wrap'},h('canvas',{id:'ch-traffic'}))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('cpu_memory')),
      h('div',{className:'chart-wrap'},h('canvas',{id:'ch-resources'}))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},h('span',null,t('user_connections'))),
      h('div',{className:'chart-wrap'},h('canvas',{id:'ch-conns'}))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('online_users')),
      S.online&&S.online.online_users&&S.online.online_users.length?
        h('div',{style:{maxHeight:'200px',overflow:'auto'}},
          h('table',{className:'tbl'},
            h('thead',null,h('tr',null,h('th',null,''),h('th',null,t('ip_address')),h('th',null,t('location')),h('th',null,t('isp')),h('th',null,t('last_seen')))),
            h('tbody',null,S.online.online_users.map(function(u){var g=u.geo||{};return h('tr',null,
                h('td',null,h('span',{className:'dot dot-on'})),
                h('td',{style:{color:'var(--tx)',fontFamily:'var(--m)',fontSize:'11px'}},u.ip||'\u2014'),
                h('td',null,g.flag?(g.flag+' '):'',g.city?(g.city+', '):'',(g.country||'')),
                h('td',{style:{fontSize:'10px',color:'var(--tx2)'}},g.isp||'\u2014'),
                h('td',null,ago(u.last_seen)))})))):
        h('div',{style:{color:'var(--tx3)',fontSize:'12px',padding:'12px 0',textAlign:'center'}},
          S.online&&S.online.live_sessions>0?t('sessions_active_no_ip'):t('no_active_conn')),
      S.online&&S.online.recently_active&&S.online.recently_active.length?h('div',{style:{marginTop:'12px',borderTop:'1px solid var(--bd)',paddingTop:'12px'}},
        h('div',{style:{fontSize:'10px',fontWeight:'600',color:'var(--tx3)',textTransform:'uppercase',letterSpacing:'.05em',marginBottom:'8px'}},t('recently_active')),
        h('div',{style:{display:'flex',flexWrap:'wrap',gap:'6px'}},S.online.recently_active.slice(0,20).map(function(u){var g=u.geo||{};return h('span',{className:'badge b-bl',style:{fontSize:'11px'}},(g.flag?g.flag+' ':'')+u.ip)}))):null),

    expandableCard('conn_log',
      h('span',{style:{display:'flex',alignItems:'center',justifyContent:'space-between',width:'100%'}},
        h('span',null,t('connection_log')),
        periodSelector(S.connPeriod,[{v:1,l:'1h'},{v:6,l:'6h'},{v:24,l:'24h'},{v:168,l:'7d'}],function(v){loadConns(v)})),
      S.conns&&S.conns.connections&&S.conns.connections.length?h('div',null,
        h('table',{className:'tbl',style:{tableLayout:'fixed',width:'100%'}},
          h('thead',null,h('tr',null,h('th',{style:{width:'14%'}},t('time')),h('th',{style:{width:'18%'}},t('ip')),h('th',{style:{width:'22%'}},t('user_agent')),h('th',{style:{width:'32%'}},t('destination')),h('th',{style:{width:'14%'}},t('event')))),
          h('tbody',null,paginatedList('connlog',S.conns.connections,function(c){return h('tr',null,
              h('td',null,ts2dt(c.ts)),
              h('td',{style:{color:c.ip?'var(--tx)':'',overflow:'hidden',textOverflow:'ellipsis'}},c.ip||''),
              h('td',{style:{overflow:'hidden',textOverflow:'ellipsis'}},c.ua||''),
              h('td',{style:{overflow:'hidden',textOverflow:'ellipsis'}},c.dst||''),
              h('td',null,h('span',{className:'badge '+(c.event==='connect'?'b-gn':c.event==='disconnect'?'b-rd':'b-bl')},c.event||'')))},25)))):
        h('div',{style:{color:'var(--tx3)',fontSize:'12px',textAlign:'center',padding:'16px'}},t('no_conn_data'))),

    S.conns&&S.conns.top_destinations&&S.conns.top_destinations.length?
      expandableCard('top_dst',t('top_destinations'),
        h('table',{className:'tbl'},
          h('thead',null,h('tr',null,h('th',null,t('domain')),h('th',{style:{textAlign:'right'}},t('connections')))),
          h('tbody',null,S.conns.top_destinations.map(function(d){return h('tr',null,h('td',null,d.dst),h('td',{style:{textAlign:'right'}},String(d.count)))})))):null,

    h('div',{className:'grid grid2',style:{gap:'14px'}},
      S.conns&&S.conns.per_client&&S.conns.per_client.length?
        expandableCard('per_client',t('traffic_per_client'),
          h('table',{className:'tbl'},
            h('thead',null,h('tr',null,h('th',null,t('client_ip')),h('th',null,t('location')),h('th',null,t('isp')),h('th',{style:{textAlign:'right'}},t('conn')),h('th',null,t('last_seen')))),
            h('tbody',null,S.conns.per_client.map(function(c){var g=c.geo||{};return h('tr',null,
              h('td',{style:{color:'var(--tx)',fontFamily:'var(--m)',fontSize:'11px'}},c.ip),
              h('td',null,g.flag?(g.flag+' '):'',g.city?(g.city+', '):'',(g.country||'')),
              h('td',{style:{fontSize:'10px',color:'var(--tx2)'}},g.isp||'\u2014'),
              h('td',{style:{textAlign:'right'}},String(c.connections)),
              h('td',null,ago(c.last_seen)))})),{margin:0})):h('div',{className:'card',style:{margin:0}},h('div',{style:{color:'var(--tx3)',fontSize:'12px',textAlign:'center',padding:'16px'}},t('no_client_data'))),
      S.conns&&S.conns.top_ports&&S.conns.top_ports.length?
        expandableCard('top_ports',t('port_breakdown'),
          h('table',{className:'tbl'},
            h('thead',null,h('tr',null,h('th',null,t('port')),h('th',null,t('svc_name')),h('th',{style:{textAlign:'right'}},t('count')))),
            h('tbody',null,S.conns.top_ports.map(function(p){var svc=p.port==='443'?'HTTPS':p.port==='80'?'HTTP':p.port==='53'?'DNS':p.port==='853'?'DoT':'';return h('tr',null,
              h('td',{style:{fontFamily:'var(--m)'}},p.port),
              h('td',null,svc?h('span',{className:'badge b-bl'},svc):''),
              h('td',{style:{textAlign:'right'}},String(p.count)))})),{margin:0})):h('div',{className:'card',style:{margin:0}},h('div',{style:{color:'var(--tx3)',fontSize:'12px',textAlign:'center',padding:'16px'}},t('no_port_data')))),

    h('div',{style:{display:'flex',justifyContent:'space-between',fontSize:'10px',color:'var(--tx3)',fontFamily:'var(--m)',marginTop:'8px',padding:'0 4px'}},
      S.conns&&S.conns.unique_ips?h('span',null,t('unique_ips')+': '+S.conns.unique_ips.length):null,
      S.dbSize?h('span',null,'DB: '+S.dbSize.db_mb+' MB | Log: '+S.dbSize.log_mb+' MB'):null)
  );
}

// ─── Users (#18 search filter) ──────────────────────────
function sortUsers(list){
  var s=S.userSort;var sorted=list.slice();
  sorted.sort(function(a,b){
    if(s==='name_asc')return a.username.localeCompare(b.username);
    if(s==='name_desc')return b.username.localeCompare(a.username);
    if(s==='date_new'){var d=(b.created_at||'').localeCompare(a.created_at||'');return d!==0?d:a.username.localeCompare(b.username)}
    if(s==='date_old'){var d=(a.created_at||'').localeCompare(b.created_at||'');return d!==0?d:a.username.localeCompare(b.username)}
    return 0});
  return sorted}
function renderUsers(){
  var aips=Object.keys(S.activeIps||{});
  var aipCount=aips.length;
  var filtered=S.users;
  if(S.userFilter){var f=S.userFilter.toLowerCase();filtered=S.users.filter(function(u){return u.username.toLowerCase().indexOf(f)!==-1})}
  filtered=sortUsers(filtered);
  var sortOpts=[{v:'name_asc',l:t('sort_name_az')},{v:'name_desc',l:t('sort_name_za')},{v:'date_new',l:t('sort_date_new')},{v:'date_old',l:t('sort_date_old')}];
  return h('div',{className:'fade-in'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'16px',gap:'12px',flexWrap:'wrap'}},
      h('div',{style:{fontSize:'13px',fontWeight:'600'}},S.users.length+' '+(S.users.length!==1?t('users_pl'):t('user'))),
      h('div',{className:'bg',style:{flex:'1',justifyContent:'flex-end'}},
        h('select',{className:'input',style:{maxWidth:'160px',padding:'6px 8px',fontSize:'11px'},value:S.userSort,onChange:function(e){S.userSort=e.target.value;R()}},sortOpts.map(function(o){return h('option',{value:o.v},o.l)})),
        h('input',{className:'input',placeholder:t('search_users'),style:{maxWidth:'200px',padding:'6px 12px',fontSize:'12px'},id:'user-search',value:S.userFilter||'',onInput:function(e){S.userFilter=e.target.value;R()}}),
        h('button',{className:'btn btn-p btn-sm',onClick:function(){S.modal={t:'add'};R()}},t('add_user')))),
    aipCount?h('div',{className:'card',style:{marginBottom:'14px'}},
      h('div',{className:'card-t'},h('span',null,aipCount+' '+(aipCount!==1?t('active_ips'):t('active_ip')))),
      h('div',{style:{display:'flex',flexWrap:'wrap',gap:'8px'}},aips.map(function(ip){
        var info=S.activeIps[ip];
        return h('div',{className:'badge b-gn',style:{fontSize:'11px',padding:'4px 10px'}},
          h('span',{className:'dot dot-on',style:{width:'6px',height:'6px'}}),ip+' ('+info.connections+' '+t('conn')+', '+ago(info.last_seen)+')')}))):null,
    h('div',{id:'user-list'},filtered.map(function(u){return renderUserCard(u)})));
}
function renderUserCard(u){var dis=u.enabled===false;var created=u.created_at?u.created_at.replace('T',' ').substring(0,16):'';
  return h('div',{className:'uc'+(dis?' uc-dis':'')},
  h('div',{className:'ui'},
    h('div',{className:'ua'+(dis?' ua-dis':'')},u.username[0].toUpperCase()),
    h('div',null,
      h('div',{style:{display:'flex',alignItems:'center',gap:'6px'}},
        h('span',{className:'un'+(dis?' un-dis':'')},u.username),
        dis?h('span',{className:'badge b-rd',style:{fontSize:'9px'}},t('user_disabled')):null),
      created?h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginTop:'1px'}},t('created_label')+': '+created):null,
      u.password?h('div',{style:{display:'flex',alignItems:'center',gap:'4px',marginTop:'2px'}},
        h('span',{className:'up',style:{cursor:'pointer'},onClick:function(e){var sp=e.target;if(sp.textContent==='\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'){sp.textContent=u.password;copyPassword(u.password)}else{sp.textContent='\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'}}},'\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'),
        h('span',{style:{cursor:'pointer',fontSize:'12px',color:'var(--tx3)'},title:t('copy'),onClick:function(){copyPassword(u.password)}},'\u{1F4CB}')):null)),
  h('div',{className:'uact'},
    h('button',{className:'btn btn-xs',onClick:function(){showCfg(u.username,'toml')}},t('btn_config')),
    h('button',{className:'btn btn-xs',onClick:function(){showCfg(u.username,'deeplink')}},t('btn_qr')),
    h('button',{className:'btn btn-xs',onClick:function(){chgPass(u.username)}},t('btn_pass')),
    h('button',{className:'btn btn-xs'+(dis?' btn-p':''),onClick:function(e){toggleUser(u.username,e.target)}},dis?t('btn_enable'):t('btn_disable')),
    h('button',{className:'btn btn-xs btn-d',onClick:function(){deleteUser(u.username)}},t('btn_del'))))}

// ─── Settings ───────────────────────────────────────────
function renderSettings(){
  var s=S.settings;if(!s.vpn_toml&&s.vpn_toml!==''){loadSettings();return loadingView()}
  var va,ra;
  return h('div',{className:'fade-in'},
    h('div',{className:'card'},h('div',{className:'card-t'},'vpn.toml'),
      va=h('textarea',{className:'input input-m',style:{minHeight:'200px'}},s.vpn_toml||''),
      h('button',{className:'btn btn-sm',style:{marginTop:'10px'},onClick:function(){saveCfg('vpn_toml',va.value)}},t('save'))),
    h('div',{className:'card'},h('div',{className:'card-t'},'rules.toml'),
      ra=h('textarea',{className:'input input-m',style:{minHeight:'120px'}},s.rules_toml||''),
      h('button',{className:'btn btn-sm',style:{marginTop:'10px'},onClick:function(){saveCfg('rules_toml',ra.value)}},t('save'))),
    h('div',{className:'card'},h('div',{className:'card-t'},'hosts.toml ('+t('read_only')+')'),
      h('div',{className:'cb'},s.hosts_toml||'')));
}

// ─── Logs ───────────────────────────────────────────────
function renderLogs(){
  return h('div',{className:'fade-in'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'12px'}},
      h('div',{style:{fontSize:'13px',fontWeight:'600'}},t('service_logs')),
      h('button',{className:'btn btn-sm',onClick:loadLogs},t('refresh'))),
    S.logsLoading?loadingView():h('div',{className:'lb'},S.logs===null?t('click_refresh'):S.logs===''?'(empty log file)':S.logs));
}

// ─── Modal (#14 proper dialogs, #19 accessible with Escape) ─
function renderModal(){
  var m=S.modal;if(!m)return h('div');
  var close=function(){S.modal=null;R()};
  var content;
  if(m.t==='add'){
    var ni,pi;
    content=h('div',{className:'md',role:'dialog','aria-modal':'true','aria-label':t('add_vpn_user')},
      h('div',{className:'md-t'},t('add_vpn_user')),
      h('div',{className:'fg'},h('label',{className:'fl'},t('username')),ni=h('input',{className:'input',placeholder:'e.g. phone-maks'})),
      h('div',{className:'fg'},h('label',{className:'fl'},t('password_empty_auto')),pi=h('input',{className:'input input-m',placeholder:'auto'})),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(){addUser(ni.value,pi.value)}},t('create')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
    setTimeout(function(){if(ni)ni.focus()},50);
  } else if(m.t==='cfg'){
    content=h('div',{className:'md',role:'dialog','aria-modal':'true','aria-label':t('config')},
      h('div',{className:'md-t'},t('config_for')+': '+m.u+' ('+m.f+')'),
      m.f==='deeplink'?h('div',{className:'qc'},h('div',{className:'qr',id:'qr-t'}),
        h('div',{style:{fontSize:'11px',color:'var(--tx3)',textAlign:'center',wordBreak:'break-all',maxWidth:'300px',marginTop:'4px'}},m.c)):
        h('div',{className:'cb'},m.c),
      h('div',{className:'bg',style:{marginTop:'14px'}},
        h('button',{className:'btn btn-p btn-sm',onClick:function(){if(navigator.clipboard)navigator.clipboard.writeText(m.c);toast(t('copied'))}},t('copy')),
        h('button',{className:'btn btn-sm',onClick:close},t('close'))));
  } else if(m.t==='confirm'){
    content=h('div',{className:'md',role:'alertdialog','aria-modal':'true','aria-label':m.title||t('confirm')},
      h('div',{className:'md-t'},m.title||t('confirm')),
      h('div',{style:{fontSize:'13px',color:'var(--tx2)',marginBottom:'16px'}},m.msg||''),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-d',onClick:function(e){if(m.onConfirm)m.onConfirm(e.currentTarget)}},t('confirm')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
  } else if(m.t==='chgpass'){
    var pi2;
    content=h('div',{className:'md',role:'dialog','aria-modal':'true','aria-label':t('change_password')},
      h('div',{className:'md-t'},t('change_password')+': "'+m.u+'"'),
      h('div',{className:'fg'},h('label',{className:'fl'},t('new_password')),pi2=h('input',{className:'input input-m',type:'password',placeholder:t('new_password')})),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(e){doChgPass(m.u,pi2.value,e.currentTarget)}},t('change')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
    setTimeout(function(){if(pi2)pi2.focus()},50);
  } else if(m.t==='chgadmin'){
    var ap;
    content=h('div',{className:'md',role:'dialog','aria-modal':'true','aria-label':t('change_password')},
      h('div',{className:'md-t'},t('change_password')),
      h('div',{className:'fg'},h('label',{className:'fl'},t('new_admin_password')),ap=h('input',{className:'input',type:'password',placeholder:t('new_admin_password')})),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(e){doChgAdmin(ap.value,e.currentTarget)}},t('change')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
    setTimeout(function(){if(ap)ap.focus()},50);
  }
  return h('div',{className:'mo',onClick:function(e){if(e.target.className&&e.target.className.indexOf&&e.target.className.indexOf('mo')!==-1)close()}},content||h('div'));
}

// (#19) Escape key closes modals
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&S.modal){S.modal=null;R()}});

// Update monitor tab non-chart sections without full re-render (prevents chart flicker)
function _updateMonitorNonChart(){
  try{
    // Update online users badge
    var badges=document.querySelectorAll('.badge.b-gn');
    for(var i=0;i<badges.length;i++){
      var b=badges[i];
      if(b.textContent.indexOf(t('sessions'))!==-1||b.textContent.indexOf('sessions')!==-1){
        b.textContent=String(S.online?S.online.live_sessions||0:0)+' '+t('sessions');
      }
    }
    // Update session count in header
    if(S.status&&S.status.live){
      var nowBadges=document.querySelectorAll('.badge.b-gn');
      for(var j=0;j<nowBadges.length;j++){
        if(nowBadges[j].textContent.indexOf(t('now'))!==-1||nowBadges[j].textContent.indexOf('now')!==-1){
          nowBadges[j].textContent=String(S.status.live.sessions||0)+' '+t('now');
        }
      }
    }
  }catch(e){}
}

// ─── Init ───────────────────────────────────────────────
applyTheme();
checkAuth();
// (#12) Auto-refresh pause when tab hidden
var _refreshDash,_refreshMon;
function startRefreshTimers(){
  _refreshDash=setInterval(async function(){if(S.auth&&S.tab==='dashboard'){await Promise.all([_loadDash(),_loadSummary(),_checkPendingReload()]);R()}},30000);
  _refreshMon=setInterval(async function(){if(S.auth&&S.tab==='monitor'){await Promise.all([_loadHistory(),_loadTraffic(),_loadConnTimeline(),_loadOnline(),_loadConns()]);R(function(){drawMonitorCharts();_updateMonitorNonChart()})}},60000);
}
function stopRefreshTimers(){if(_refreshDash){clearInterval(_refreshDash);_refreshDash=null}if(_refreshMon){clearInterval(_refreshMon);_refreshMon=null}}
startRefreshTimers();
document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden'){stopRefreshTimers()}else{startRefreshTimers()}});
</script>
</body>
</html>"""
