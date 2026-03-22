FRONTEND_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5">
<title>TrustTunnel Client</title>
<link rel="icon" type="image/png" sizes="64x64" href="/static/favicon.png?v=2">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" crossorigin="anonymous">
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
.logo-img{transition:filter .3s;object-fit:contain}
[data-theme="dark"] .logo-img{filter:brightness(0) invert(1)}
@media(prefers-color-scheme:dark){[data-theme="system"] .logo-img{filter:brightness(0) invert(1)}}
[data-theme="light"] .toast-ok{background:#f0fdf4;border:1px solid #86efac;color:#16a34a}
[data-theme="light"] .toast-err{background:#fef2f2;border:1px solid #fca5a5;color:#dc2626}
@media(prefers-color-scheme:light){
  [data-theme="system"] .toast-ok{background:#f0fdf4;border:1px solid #86efac;color:#16a34a}
  [data-theme="system"] .toast-err{background:#fef2f2;border:1px solid #fca5a5;color:#dc2626}
}
[data-theme="light"] .btn-d{background:#fef2f2;border-color:#fca5a5;color:#dc2626}
[data-theme="light"] .btn-d:hover{background:#fee2e2}
@media(prefers-color-scheme:light){
  [data-theme="system"] .btn-d{background:#fef2f2;border-color:#fca5a5;color:#dc2626}
  [data-theme="system"] .btn-d:hover{background:#fee2e2}
}
body{background:var(--bg);color:var(--tx);font-family:var(--f);min-height:100vh;-webkit-font-smoothing:antialiased}
input,textarea,select,button{font-family:inherit;font-size:inherit}
::-webkit-scrollbar{width:5px;height:5px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--bd);border-radius:3px}
::selection{background:var(--ac2);color:#fff}
.app{max-width:1000px;margin:0 auto;padding:16px}
@media(min-width:768px){.app{padding:24px 32px}}
.hdr{display:flex;align-items:center;justify-content:space-between;padding:14px 0 18px;margin-bottom:16px;gap:8px;flex-wrap:wrap}
.logo{display:flex;align-items:center;gap:12px}
.logo-t{font-size:17px;font-weight:700;letter-spacing:-.03em}
.logo-s{font-size:11px;color:var(--tx3);font-family:var(--m)}
.tg{display:inline-flex;gap:1px;background:var(--sf);border:1px solid var(--bd);border-radius:6px;padding:2px;margin-right:6px}
.tg button{padding:3px 7px;border:none;border-radius:4px;background:transparent;color:var(--tx3);cursor:pointer;font-size:11px;transition:.15s;line-height:1}
.tg button:hover{color:var(--tx2)}
.tg button.on{background:var(--sf2);color:var(--ac);box-shadow:0 1px 3px rgba(0,0,0,.15)}
.lg{display:inline-flex;gap:1px;background:var(--sf);border:1px solid var(--bd);border-radius:6px;padding:2px;margin-right:6px}
.lg button{padding:3px 7px;border:none;border-radius:4px;background:transparent;color:var(--tx3);cursor:pointer;font-size:11px;font-weight:600;transition:.15s;line-height:1}
.lg button:hover{color:var(--tx2)}
.lg button.on{background:var(--sf2);color:var(--ac);box-shadow:0 1px 3px rgba(0,0,0,.15)}
.tabs{display:flex;gap:2px;margin-bottom:18px;background:var(--sf);border-radius:10px;padding:3px;border:1px solid var(--bd);overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:1;min-width:0;padding:8px 10px;border-radius:8px;border:none;background:transparent;color:var(--tx3);cursor:pointer;font-size:12px;font-weight:600;white-space:nowrap;transition:all .2s;text-align:center}
.tab:hover{color:var(--tx2)}
.tab.on{background:var(--sf2);color:var(--tx);box-shadow:var(--shadow)}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:18px;margin-bottom:14px;box-shadow:var(--shadow)}
.card-t{font-size:12px;font-weight:600;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;color:var(--tx2);text-transform:uppercase;letter-spacing:.05em}
.grid{display:grid;gap:10px}.grid2{grid-template-columns:1fr 1fr}.grid3{grid-template-columns:1fr 1fr 1fr}
@media(max-width:640px){.grid2,.grid3{grid-template-columns:1fr}}
.stat{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:14px 16px;position:relative;overflow:hidden;transition:border-color .2s}
.stat:hover{border-color:var(--bd2)}
.stat-l{font-size:10px;color:var(--tx3);text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin-bottom:6px}
.stat-v{font-size:20px;font-weight:700;font-family:var(--m);letter-spacing:-.02em;line-height:1.2}
.stat-v.on{color:var(--gn)}.stat-v.off{color:var(--rd)}
.stat-green{background:var(--gnbg);border-color:rgba(34,197,94,.15)}
.stat-red{background:var(--rdbg);border-color:rgba(239,68,68,.15)}
.btn{display:inline-flex;align-items:center;gap:5px;padding:7px 14px;border-radius:var(--r2);border:1px solid var(--bd);background:var(--sf2);color:var(--tx);font-size:12px;font-weight:500;cursor:pointer;transition:all .15s;white-space:nowrap}
.btn:hover{border-color:var(--bd2);background:var(--sf3)}
.btn:disabled{opacity:.5;cursor:not-allowed}
.btn-p{background:var(--ac2);border-color:var(--ac2);color:#fff}.btn-p:hover{background:var(--ac)}
.btn-d{background:var(--rd2);border-color:#9e2a2a;color:#fca5a5}.btn-d:hover{background:#991b1b}
.btn-sm{padding:4px 10px;font-size:11px;border-radius:6px}
.btn-xs{padding:3px 8px;font-size:10px;border-radius:5px}
.btn-ghost{background:transparent;border-color:transparent}.btn-ghost:hover{background:var(--sf2);border-color:var(--bd)}
.bg{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.input{width:100%;padding:10px 14px;border-radius:var(--r2);border:1px solid var(--bd);background:var(--bg);color:var(--tx);font-size:13px;outline:none;transition:border-color .2s}
.input:focus{border-color:var(--ac);box-shadow:0 0 0 3px rgba(59,158,255,.1)}
textarea.input{resize:vertical;min-height:80px}.input-m{font-family:var(--m);font-size:12px}
.fg{margin-bottom:14px}.fl{display:block;font-size:10px;font-weight:600;color:var(--tx3);margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em}
.badge{display:inline-block;padding:2px 8px;border-radius:5px;font-size:10px;font-weight:600;font-family:var(--m)}
.b-gn{background:rgba(34,197,94,.12);color:var(--gn)}
.b-rd{background:rgba(239,68,68,.12);color:var(--rd)}
.b-bl{background:rgba(59,158,255,.12);color:var(--ac)}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;flex-shrink:0}
.dot-on{background:var(--gn);box-shadow:0 0 6px var(--gn)}
.dot-off{background:var(--rd);box-shadow:0 0 6px rgba(239,68,68,.4)}
.mo{position:fixed;inset:0;background:rgba(0,0,0,.75);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;z-index:100;padding:16px}
.md{background:var(--sf);border:1px solid var(--bd);border-radius:16px;padding:24px;width:calc(100% - 32px);max-width:480px;max-height:90vh;overflow:auto;box-shadow:0 8px 40px rgba(0,0,0,.5)}
.md-t{font-size:16px;font-weight:700;margin-bottom:16px}
.toast{position:fixed;top:16px;right:16px;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:500;z-index:9999;box-shadow:0 4px 20px rgba(0,0,0,.4);animation:slideIn .2s}
@keyframes slideIn{from{transform:translateX(20px);opacity:0}to{transform:none;opacity:1}}
.toast-ok{background:#052e16;border:1px solid #166534;color:var(--gn)}.toast-err{background:#450a0a;border:1px solid #991b1b;color:var(--rd)}
.lw{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;background:radial-gradient(ellipse at 50% 30%,rgba(59,158,255,.05),transparent 60%)}
.lc{width:100%;max-width:380px;padding:32px;background:var(--sf);border:1px solid var(--bd);border-radius:18px;box-shadow:var(--glow),var(--shadow)}
.lt{font-size:22px;font-weight:700;text-align:center;margin-bottom:6px;letter-spacing:-.02em}
.ls{font-size:12px;color:var(--tx3);text-align:center;margin-bottom:24px}
.tbl-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tbl{width:100%;border-collapse:collapse;font-size:11px}
.tbl th{text-align:left;padding:8px 10px;border-bottom:1px solid var(--bd);color:var(--tx3);font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.05em;background:var(--bg)}
.tbl td{padding:7px 10px;border-bottom:1px solid rgba(30,42,58,.5);color:var(--tx2);font-family:var(--m);font-size:11px}
.tbl tr:hover td{background:rgba(59,158,255,.03)}
.tbl th:first-child{border-radius:6px 0 0 0}.tbl th:last-child{border-radius:0 6px 0 0}
.loading-box{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:60px 0;color:var(--tx3);font-size:13px;font-weight:500}
@keyframes spin{to{transform:rotate(360deg)}}
.spinner{width:16px;height:16px;border:2px solid var(--bd);border-top-color:var(--ac);border-radius:50%;animation:spin .6s linear infinite}
.spinner-lg{width:28px;height:28px;border-width:2.5px}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.fade-in{animation:fadeIn .3s ease-out}
.tab-content{animation:tabFade .25s ease-out}
@keyframes tabFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.pulse{animation:pulse 2s ease-in-out infinite}
.sc{background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);padding:16px;margin-bottom:10px;display:flex;align-items:center;justify-content:space-between;gap:10px;transition:border-color .2s}
.sc:hover{border-color:var(--bd2)}
.sc-active{border-left:3px solid var(--gn)}
.sc-dis{opacity:.5;border-style:dashed}
.sc-info{flex:1;min-width:0}
.sc-name{font-weight:600;font-size:14px}
.sc-host{font-size:11px;color:var(--tx3);font-family:var(--m)}
.sc-acts{display:flex;gap:4px;flex-shrink:0;flex-wrap:wrap}
@media(max-width:640px){.sc{flex-direction:column;align-items:stretch}.sc-acts{justify-content:flex-start}}
.status-bar{display:flex;align-items:center;gap:10px;padding:14px 18px;background:var(--sf);border:1px solid var(--bd);border-radius:var(--r);margin-bottom:14px;flex-wrap:wrap}
.toggle{position:relative;width:40px;height:22px;cursor:pointer}
.toggle input{opacity:0;width:0;height:0}
.toggle .slider{position:absolute;inset:0;background:var(--sf3);border-radius:11px;transition:.2s;border:1px solid var(--bd)}
.toggle .slider:before{content:'';position:absolute;width:16px;height:16px;left:2px;bottom:2px;background:var(--tx3);border-radius:50%;transition:.2s}
.toggle input:checked+.slider{background:var(--ac2);border-color:var(--ac2)}
.toggle input:checked+.slider:before{transform:translateX(18px);background:#fff}
.add-tabs{display:flex;gap:2px;margin-bottom:12px;background:var(--bg);border-radius:7px;padding:2px;border:1px solid var(--bd)}
.add-tab{flex:1;padding:6px;border:none;border-radius:5px;background:transparent;color:var(--tx3);cursor:pointer;font-size:11px;font-weight:600;transition:.15s;text-align:center}
.add-tab.on{background:var(--sf2);color:var(--ac)}
select.input{appearance:auto}
</style>
</head>
<body>
<div id="root"></div>
<script>
var T={en:{
  servers:'Servers',monitor:'Monitor',settings:'Settings',
  connected:'Connected',disconnected:'Disconnected',connecting:'Connecting...',
  active:'Active',activate:'Activate',edit:'Edit',delete:'Delete',
  add_server:'Add server',deeplink:'Deeplink',manual:'Manual',
  hostname:'Hostname',address:'Address',username:'Username',password:'Password',
  protocol:'Protocol',priority:'Priority',name:'Name',
  paste_deeplink:'Paste tt:// link here',
  server_added:'Server added',server_deleted:'Server deleted',
  activating:'Activating...',activation_ok:'Connected',activation_fail:'Connection failed',
  failover_log:'Failover history',from_server:'From',to_server:'To',reason:'Reason',
  no_failover_log:'No failover events',
  health_check:'Health check',interval:'Interval',auto_failover:'Auto-failover',
  threshold:'Threshold',failures:'failures',
  vpn_mode:'VPN mode',general:'General',selective:'Selective',
  killswitch:'Kill switch',dns:'DNS upstreams',exclusions_label:'Exclusions',
  mtu:'MTU',save:'Save',saved:'Saved',
  change_password:'Change password',new_password:'New password',
  tun_ip:'Tunnel IP',latency:'Latency',uptime:'Uptime',
  service_controls:'Service controls',restart:'Restart',stop:'Stop',start:'Start',
  sign_in:'Sign in',enter_admin_pw:'Enter admin password',
  create_admin_pw:'Create admin password',create_password:'Create password',
  initial_setup:'Initial Setup',loading:'Loading...',logout:'Logout',
  password_btn:'Password',cancel:'Cancel',confirm:'Confirm',
  delete_confirm:'Delete this server?',
  move_up:'Up',move_down:'Down',enabled:'Enabled',disabled:'Disabled',
  no_servers:'No servers added yet',
  theme_dark:'Dark',theme_light:'Light',theme_system:'System',
  prev:'Prev',next:'Next',page:'Page'
},ru:{
  servers:'\u0421\u0435\u0440\u0432\u0435\u0440\u044b',monitor:'\u041c\u043e\u043d\u0438\u0442\u043e\u0440',settings:'\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438',
  connected:'\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u043e',disconnected:'\u041e\u0442\u043a\u043b\u044e\u0447\u0435\u043d\u043e',connecting:'\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435...',
  active:'\u0410\u043a\u0442\u0438\u0432\u043d\u044b\u0439',activate:'\u0410\u043a\u0442\u0438\u0432\u0438\u0440\u043e\u0432\u0430\u0442\u044c',edit:'\u0420\u0435\u0434\u0430\u043a\u0442.',delete:'\u0423\u0434\u0430\u043b\u0438\u0442\u044c',
  add_server:'\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0441\u0435\u0440\u0432\u0435\u0440',deeplink:'Deeplink',manual:'\u0412\u0440\u0443\u0447\u043d\u0443\u044e',
  hostname:'\u0425\u043e\u0441\u0442',address:'\u0410\u0434\u0440\u0435\u0441',username:'\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c',password:'\u041f\u0430\u0440\u043e\u043b\u044c',
  protocol:'\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b',priority:'\u041f\u0440\u0438\u043e\u0440\u0438\u0442\u0435\u0442',name:'\u0418\u043c\u044f',
  paste_deeplink:'\u0412\u0441\u0442\u0430\u0432\u044c\u0442\u0435 tt:// \u0441\u0441\u044b\u043b\u043a\u0443',
  server_added:'\u0421\u0435\u0440\u0432\u0435\u0440 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d',server_deleted:'\u0421\u0435\u0440\u0432\u0435\u0440 \u0443\u0434\u0430\u043b\u0451\u043d',
  activating:'\u0410\u043a\u0442\u0438\u0432\u0430\u0446\u0438\u044f...',activation_ok:'\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u043e',activation_fail:'\u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u043e\u0434\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f',
  failover_log:'\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0439',from_server:'\u041e\u0442\u043a\u0443\u0434\u0430',to_server:'\u041a\u0443\u0434\u0430',reason:'\u041f\u0440\u0438\u0447\u0438\u043d\u0430',
  no_failover_log:'\u041d\u0435\u0442 \u0441\u043e\u0431\u044b\u0442\u0438\u0439 \u043f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f',
  health_check:'\u041f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0437\u0434\u043e\u0440\u043e\u0432\u044c\u044f',interval:'\u0418\u043d\u0442\u0435\u0440\u0432\u0430\u043b',auto_failover:'\u0410\u0432\u0442\u043e-\u043f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435',
  threshold:'\u041f\u043e\u0440\u043e\u0433',failures:'\u043e\u0448\u0438\u0431\u043e\u043a',
  vpn_mode:'\u0420\u0435\u0436\u0438\u043c VPN',general:'\u041e\u0431\u0449\u0438\u0439',selective:'\u0412\u044b\u0431\u043e\u0440\u043e\u0447\u043d\u044b\u0439',
  killswitch:'Kill switch',dns:'DNS',exclusions_label:'\u0418\u0441\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u044f',
  mtu:'MTU',save:'\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c',saved:'\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e',
  change_password:'\u0421\u043c\u0435\u043d\u0438\u0442\u044c \u043f\u0430\u0440\u043e\u043b\u044c',new_password:'\u041d\u043e\u0432\u044b\u0439 \u043f\u0430\u0440\u043e\u043b\u044c',
  tun_ip:'Tunnel IP',latency:'\u0417\u0430\u0434\u0435\u0440\u0436\u043a\u0430',uptime:'\u0410\u043f\u0442\u0430\u0439\u043c',
  service_controls:'\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435',restart:'\u041f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u043a',stop:'\u0421\u0442\u043e\u043f',start:'\u0417\u0430\u043f\u0443\u0441\u043a',
  sign_in:'\u0412\u043e\u0439\u0442\u0438',enter_admin_pw:'\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043f\u0430\u0440\u043e\u043b\u044c \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430',
  create_admin_pw:'\u0421\u043e\u0437\u0434\u0430\u0439\u0442\u0435 \u043f\u0430\u0440\u043e\u043b\u044c \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430',create_password:'\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043f\u0430\u0440\u043e\u043b\u044c',
  initial_setup:'\u041d\u0430\u0447\u0430\u043b\u044c\u043d\u0430\u044f \u043d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0430',loading:'\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430...',logout:'\u0412\u044b\u0445\u043e\u0434',
  password_btn:'\u041f\u0430\u0440\u043e\u043b\u044c',cancel:'\u041e\u0442\u043c\u0435\u043d\u0430',confirm:'\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c',
  delete_confirm:'\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u044d\u0442\u043e\u0442 \u0441\u0435\u0440\u0432\u0435\u0440?',
  move_up:'\u0412\u0432\u0435\u0440\u0445',move_down:'\u0412\u043d\u0438\u0437',enabled:'\u0412\u043a\u043b.',disabled:'\u0412\u044b\u043a\u043b.',
  no_servers:'\u0421\u0435\u0440\u0432\u0435\u0440\u044b \u0435\u0449\u0451 \u043d\u0435 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u044b',
  theme_dark:'\u0422\u0451\u043c\u043d\u0430\u044f',theme_light:'\u0421\u0432\u0435\u0442\u043b\u0430\u044f',theme_system:'\u0421\u0438\u0441\u0442\u0435\u043c\u0430',
  prev:'\u041d\u0430\u0437\u0430\u0434',next:'\u0412\u043f\u0435\u0440\u0451\u0434',page:'\u0421\u0442\u0440.'
}};

var A='/api';
var S={auth:false,setup:false,loading:true,tab:'servers',
  servers:[],activeServerId:'',status:null,failoverLog:[],settings:{},
  toast:null,modal:null,lang:localStorage.getItem('tt_lang')||'en',
  theme:localStorage.getItem('tt_theme')||'system',addMode:'deeplink',flPage:0};

function t(k){return(T[S.lang]||T.en)[k]||T.en[k]||k}
function setLang(l){S.lang=l;localStorage.setItem('tt_lang',l);R()}
function setTheme(th){S.theme=th;localStorage.setItem('tt_theme',th);applyTheme();R()}
function applyTheme(){document.documentElement.setAttribute('data-theme',S.theme)}

async function api(p,o){o=o||{};var r=await fetch(A+p,{headers:{'Content-Type':'application/json'},credentials:'same-origin',...o});var d=await r.json();if(!r.ok)throw new Error(d.detail||r.statusText);return d}
function toast(m,e){S.toast={m:m,e:!!e};R();setTimeout(function(){S.toast=null;R()},3500)}
function fmtUptime(sec){if(!sec)return '\u2014';var d=Math.floor(sec/86400),h=Math.floor((sec%86400)/3600),m=Math.floor((sec%3600)/60);if(d>0)return d+'d '+h+'h '+m+'m';if(h>0)return h+'h '+m+'m';return m+'m'}
function withLoading(btn,fn){if(!btn)return fn();var orig=btn.textContent;btn.disabled=true;btn.textContent='...';return Promise.resolve(fn()).finally(function(){if(btn.parentNode){btn.disabled=false;btn.textContent=orig}})}

function h(t,a){var e=document.createElement(t);var dv=null;if(a){var ks=Object.keys(a);for(var i=0;i<ks.length;i++){var k=ks[i],v=a[k];if(k==='style'&&typeof v==='object')Object.assign(e.style,v);else if(k.substr(0,2)==='on')e.addEventListener(k.slice(2).toLowerCase(),v);else if(k==='className')e.className=v;else if(k==='value'){dv=v}else if(k==='checked'||k==='selected'||k==='disabled'){if(v!==false&&v!=null)e[k]=v}else e.setAttribute(k,v)}}for(var i=2;i<arguments.length;i++){var x=arguments[i];if(Array.isArray(x)){for(var j=0;j<x.length;j++)an(e,x[j])}else an(e,x)}if(dv!==null)e.value=dv;return e}
function an(e,x){if(x==null||x===false||x===undefined)return;if(typeof x==='number')x=String(x);if(typeof x==='string')e.appendChild(document.createTextNode(x));else if(x.nodeType)e.appendChild(x);else if(Array.isArray(x)){for(var i=0;i<x.length;i++)an(e,x[i])}}

async function checkAuth(){try{var r=await api('/auth-status');S.auth=r.authenticated;S.setup=r.setup_required}catch(e){S.auth=false}S.loading=false;R()}
async function doLogin(pw){try{await api('/login',{method:'POST',body:JSON.stringify({password:pw})});S.auth=true;loadAll()}catch(e){toast(e.message,true)}R()}
async function doSetup(pw){try{await api('/setup',{method:'POST',body:JSON.stringify({password:pw})});S.setup=false;await doLogin(pw)}catch(e){toast(e.message,true)}}
async function doLogout(){await api('/logout',{method:'POST'});S.auth=false;R()}

async function loadAll(){await Promise.all([loadServers(),loadStatus()]);R()}
async function loadServers(){try{var r=await api('/servers');S.servers=r.servers||[];S.activeServerId=r.active_server_id||''}catch(e){toast(e.message,true)}}
async function loadStatus(){try{S.status=await api('/status')}catch(e){}}
async function loadFailoverLog(){try{var r=await api('/failover-log');S.failoverLog=r.log||[]}catch(e){toast(e.message,true)}R()}
async function loadSettings(){try{var r=await api('/settings');S.settings=r.settings||r||{}}catch(e){toast(e.message,true)}R()}

async function addServer(data){try{await api('/servers',{method:'POST',body:JSON.stringify(data)});toast(t('server_added'));await loadAll();R()}catch(e){toast(e.message,true)}}
async function deleteServer(id){S.modal={t:'confirm',title:t('delete'),msg:t('delete_confirm'),onOk:async function(btn){await withLoading(btn,async function(){try{await api('/servers/'+id,{method:'DELETE'});toast(t('server_deleted'));S.modal=null;await loadAll();R()}catch(e){toast(e.message,true)}})}};R()}
async function activateServer(id,btn){await withLoading(btn,async function(){try{var r=await api('/servers/'+id+'/activate',{method:'POST'});toast(r.ok?t('activation_ok'):t('activation_fail'),!r.ok);await loadAll();R()}catch(e){toast(e.message,true)}})}
async function editServer(id,data){try{await api('/servers/'+id,{method:'PUT',body:JSON.stringify(data)});toast(t('saved'));S.modal=null;await loadAll();R()}catch(e){toast(e.message,true)}}
async function reorderServers(order){try{await api('/servers/reorder',{method:'PUT',body:JSON.stringify({order:order})})}catch(e){toast(e.message,true)}}
async function svcAct(a,btn){await withLoading(btn,async function(){try{await api('/service/'+a,{method:'POST'});toast(a+' ok');setTimeout(loadStatus,2000)}catch(e){toast(e.message,true)}})}
async function saveSettings(data){try{await api('/settings',{method:'PUT',body:JSON.stringify(data)});toast(t('saved'))}catch(e){toast(e.message,true)}}
async function chgAdmin(pw,btn){await withLoading(btn,async function(){try{await api('/change-password',{method:'POST',body:JSON.stringify({password:pw})});toast(t('saved'));S.modal=null;S.auth=false;R()}catch(e){toast(e.message,true)}})}

var _rTimer=null;
function R(){if(_rTimer)return;_rTimer=requestAnimationFrame(function(){_rTimer=null;_doRender()})}
function _doRender(){
  var root=document.getElementById('root');
  try{
    var frag=document.createDocumentFragment();
    if(S.toast)frag.appendChild(h('div',{className:'toast '+(S.toast.e?'toast-err':'toast-ok')},S.toast.m));
    if(S.modal)frag.appendChild(renderModal());
    if(S.loading){frag.appendChild(h('div',{className:'loading-box',style:{minHeight:'60vh'}},h('div',{className:'spinner spinner-lg'}),t('loading')));root.replaceChildren(frag);return}
    if(!S.auth){frag.appendChild(renderLogin());root.replaceChildren(frag);return}
    frag.appendChild(renderApp());
    root.replaceChildren(frag);
  }catch(err){console.error('R() error:',err)}
}

function langThemeBar(){
  return h('div',{style:{display:'flex',justifyContent:'center',marginTop:'16px',gap:'8px'}},
    h('div',{className:'lg'},
      h('button',{className:S.lang==='en'?'on':'',onClick:function(){setLang('en')}},'EN'),
      h('button',{className:S.lang==='ru'?'on':'',onClick:function(){setLang('ru')}},'\u0420\u0423')),
    h('div',{className:'tg'},
      h('button',{className:S.theme==='dark'?'on':'',onClick:function(){setTheme('dark')}},'\u263E'),
      h('button',{className:S.theme==='light'?'on':'',onClick:function(){setTheme('light')}},'\u2600'),
      h('button',{className:S.theme==='system'?'on':'',onClick:function(){setTheme('system')}},'\u2699')))
}

function renderLogin(){
  var pw;var isS=S.setup;
  var card=h('div',{className:'lw'},h('div',{className:'lc'},
    h('div',{style:{textAlign:'center',marginBottom:'20px'}},h('img',{src:'/static/logo-full.png',className:'logo-img',style:{maxHeight:'56px',maxWidth:'260px',width:'auto',height:'auto',margin:'0 auto 12px'}})),
    h('div',{className:'lt'},isS?t('initial_setup'):''),
    h('div',{className:'ls'},isS?t('create_admin_pw'):t('enter_admin_pw')),
    h('div',{className:'fg'},pw=h('input',{className:'input',type:'password',placeholder:t('password'),style:{textAlign:'center'}})),
    h('button',{className:'btn btn-p',style:{width:'100%',justifyContent:'center',padding:'12px',fontSize:'13px',borderRadius:'10px'},onClick:function(){isS?doSetup(pw.value):doLogin(pw.value)}},isS?t('create_password'):t('sign_in')),
    langThemeBar()));
  setTimeout(function(){if(pw){pw.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();(isS?doSetup:doLogin)(pw.value)}});pw.focus()}},50);
  return card;
}

function renderApp(){
  var tabs=[{id:'servers',label:t('servers')},{id:'monitor',label:t('monitor')},{id:'settings',label:t('settings')}];
  return h('div',{className:'app fade-in'},
    h('div',{className:'hdr'},
      h('div',{className:'logo'},
        h('img',{src:'/static/logo-full.png',className:'logo-img',style:{height:'34px',width:'auto'}}),
        h('div',{className:'logo-s',style:{marginLeft:'8px'}},'Client')),
      h('div',{className:'bg'},
        h('div',{className:'lg'},
          h('button',{className:S.lang==='en'?'on':'',onClick:function(){setLang('en')}},'EN'),
          h('button',{className:S.lang==='ru'?'on':'',onClick:function(){setLang('ru')}},'\u0420\u0423')),
        h('div',{className:'tg'},
          h('button',{className:S.theme==='dark'?'on':'',onClick:function(){setTheme('dark')}},'\u263E'),
          h('button',{className:S.theme==='light'?'on':'',onClick:function(){setTheme('light')}},'\u2600'),
          h('button',{className:S.theme==='system'?'on':'',onClick:function(){setTheme('system')}},'\u2699')),
        h('button',{className:'btn btn-xs btn-ghost',onClick:function(){S.modal={t:'chgadmin'};R()}},t('password_btn')),
        h('button',{className:'btn btn-xs btn-ghost',onClick:doLogout},t('logout')))),
    h('div',{className:'tabs'},tabs.map(function(tb){return h('button',{className:'tab'+(S.tab===tb.id?' on':''),
      onClick:function(){S.tab=tb.id;if(tb.id==='servers')loadAll();if(tb.id==='monitor'){loadStatus();loadFailoverLog()}if(tb.id==='settings')loadSettings();R()}},tb.label)})),
    h('div',{className:'tab-content'},S.tab==='servers'?renderServers():S.tab==='monitor'?renderMonitor():renderSettings()));
}

function renderModal(){
  var m=S.modal;if(!m)return h('div');
  var close=function(){S.modal=null;R()};
  var content;
  if(m.t==='confirm'){
    content=h('div',{className:'md'},
      h('div',{className:'md-t'},m.title||t('confirm')),
      h('div',{style:{fontSize:'13px',color:'var(--tx2)',marginBottom:'16px'}},m.msg||''),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-d',onClick:function(e){if(m.onOk)m.onOk(e.currentTarget)}},t('confirm')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
  }else if(m.t==='edit'){
    var ni,hi,ui,pi,proto;var s=m.s;
    content=h('div',{className:'md'},
      h('div',{className:'md-t'},t('edit')+': '+s.name),
      h('div',{className:'fg'},h('label',{className:'fl'},t('name')),ni=h('input',{className:'input',value:s.name||''})),
      h('div',{className:'fg'},h('label',{className:'fl'},t('hostname')),hi=h('input',{className:'input input-m',value:s.hostname||''})),
      h('div',{className:'fg'},h('label',{className:'fl'},t('username')),ui=h('input',{className:'input',value:s.username||''})),
      h('div',{className:'fg'},h('label',{className:'fl'},t('password')),pi=h('input',{className:'input',type:'password',value:s.password||''})),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(){editServer(s.id,{name:ni.value,hostname:hi.value,username:ui.value,password:pi.value})}},t('save')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
  }else if(m.t==='chgadmin'){
    var ap;
    content=h('div',{className:'md'},
      h('div',{className:'md-t'},t('change_password')),
      h('div',{className:'fg'},h('label',{className:'fl'},t('new_password')),ap=h('input',{className:'input',type:'password',placeholder:t('new_password')})),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(e){if(ap.value.length<6){toast('Min 6 chars',true);return}chgAdmin(ap.value,e.currentTarget)}},t('save')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
    setTimeout(function(){if(ap)ap.focus()},50);
  }
  return h('div',{className:'mo',onClick:function(e){if(e.target.className&&e.target.className.indexOf('mo')!==-1)close()}},content||h('div'));
}

function renderStatusBar(){
  var st=S.status;var hl=st&&st.health?st.health:{};var ok=hl.tun_up;var srv=st&&st.active_server;
  return h('div',{className:'status-bar'},
    h('span',{className:'dot '+(ok?'dot-on':'dot-off')}),
    h('span',{style:{fontWeight:600}},ok?t('connected')+(srv?' \u2014 '+srv.name:''):t('disconnected')),
    hl.latency_ms?h('span',{style:{color:'var(--tx3)',fontSize:'12px',fontFamily:'var(--m)',marginLeft:'auto'}},t('latency')+': '+hl.latency_ms+'ms'):'',
    hl.tun_ip?h('span',{style:{color:'var(--tx3)',fontSize:'12px',fontFamily:'var(--m)'}},t('tun_ip')+': '+hl.tun_ip):'');
}

function renderServers(){
  var sorted=S.servers.slice().sort(function(a,b){return(a.priority||0)-(b.priority||0)});
  return h('div',null,
    renderStatusBar(),
    sorted.length===0?h('div',{className:'card',style:{textAlign:'center',padding:'40px',color:'var(--tx3)'}},t('no_servers')):sorted.map(function(s,i){
      var isActive=s.id===S.activeServerId;
      return h('div',{className:'sc'+(isActive?' sc-active':'')+(s.disabled?' sc-dis':'')},
        h('div',{style:{display:'flex',flexDirection:'column',gap:'2px',marginRight:'10px',alignItems:'center'}},
          h('span',{style:{fontSize:'10px',color:'var(--tx3)',fontFamily:'var(--m)'}},''+(i+1)),
          h('button',{className:'btn btn-xs',disabled:i===0,onClick:function(){moveServer(i,-1)}},'\u25B2'),
          h('button',{className:'btn btn-xs',disabled:i===sorted.length-1,onClick:function(){moveServer(i,1)}},'\u25BC')),
        h('div',{className:'sc-info'},
          h('div',{style:{display:'flex',alignItems:'center',gap:'8px'}},
            h('span',{className:'sc-name'},s.name||s.hostname),
            isActive?h('span',{className:'badge b-gn'},t('active')):'',
            s.protocol?h('span',{className:'badge b-bl'},s.protocol):''),
          h('div',{className:'sc-host'},s.hostname+(s.addresses?' \u2014 '+s.addresses:''))),
        h('div',{className:'sc-acts'},
          !isActive?h('button',{className:'btn btn-sm btn-p',onClick:function(e){activateServer(s.id,e.currentTarget)}},t('activate')):'',
          h('button',{className:'btn btn-sm',onClick:function(){S.modal={t:'edit',s:s};R()}},t('edit')),
          h('button',{className:'btn btn-sm btn-d',onClick:function(){deleteServer(s.id)}},t('delete'))));
    }),
    renderAddServer());
}

function moveServer(idx,dir){
  var sorted=S.servers.slice().sort(function(a,b){return(a.priority||0)-(b.priority||0)});
  var ni=idx+dir;if(ni<0||ni>=sorted.length)return;
  var tmp=sorted[idx];sorted[idx]=sorted[ni];sorted[ni]=tmp;
  reorderServers(sorted.map(function(s){return s.id}));
  S.servers=sorted.map(function(s,i){s.priority=i;return s});R();
}

function renderAddServer(){
  var dl,hn,ad,un,pw,nm,proto;
  return h('div',{className:'card'},
    h('div',{className:'card-t'},t('add_server')),
    h('div',{className:'add-tabs'},
      h('button',{className:'add-tab'+(S.addMode==='deeplink'?' on':''),onClick:function(){S.addMode='deeplink';R()}},t('deeplink')),
      h('button',{className:'add-tab'+(S.addMode==='manual'?' on':''),onClick:function(){S.addMode='manual';R()}},t('manual'))),
    S.addMode==='deeplink'?h('div',null,
      h('div',{className:'fg'},h('label',{className:'fl'},'Deeplink'),dl=h('input',{className:'input input-m',placeholder:t('paste_deeplink')})),
      h('button',{className:'btn btn-p',onClick:function(){addServer({deeplink:dl.value})}},t('add_server'))
    ):h('div',null,
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},h('label',{className:'fl'},t('name')),nm=h('input',{className:'input'})),
        h('div',{className:'fg'},h('label',{className:'fl'},t('hostname')),hn=h('input',{className:'input input-m'}))),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},h('label',{className:'fl'},t('address')),ad=h('input',{className:'input input-m'})),
        h('div',{className:'fg'},h('label',{className:'fl'},t('protocol')),proto=h('select',{className:'input'},h('option',{value:'http2'},'HTTP/2'),h('option',{value:'http3'},'HTTP/3')))),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},h('label',{className:'fl'},t('username')),un=h('input',{className:'input'})),
        h('div',{className:'fg'},h('label',{className:'fl'},t('password')),pw=h('input',{className:'input',type:'password'}))),
      h('button',{className:'btn btn-p',onClick:function(){addServer({hostname:hn.value,addresses:ad.value,username:un.value,password:pw.value,name:nm.value,protocol:proto.value})}},t('add_server'))));
}

function renderMonitor(){
  var st=S.status;var hl=st&&st.health?st.health:{};var ok=hl.tun_up;var srv=st&&st.active_server;
  return h('div',null,
    h('div',{className:'card'},
      h('div',{className:'card-t'},t('monitor')),
      h('div',{className:'grid grid3',style:{marginBottom:'14px'}},
        h('div',{className:'stat'+(ok?' stat-green':' stat-red')},
          h('div',{className:'stat-l'},t('connected')),
          h('div',{className:'stat-v '+(ok?'on':'off')},ok?t('connected'):t('disconnected'))),
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('active')),
          h('div',{className:'stat-v'},srv?srv.name:'\u2014')),
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('latency')),
          h('div',{className:'stat-v'},hl.latency_ms?hl.latency_ms+'ms':'\u2014'))),
      h('div',{className:'grid grid3'},
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('tun_ip')),
          h('div',{className:'stat-v',style:{fontSize:'14px'}},hl.tun_ip?hl.tun_ip:'\u2014')),
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('uptime')),
          h('div',{className:'stat-v',style:{fontSize:'14px'}},fmtUptime(st?st.uptime_seconds:0))),
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('hostname')),
          h('div',{className:'stat-v',style:{fontSize:'14px'}},srv?srv.hostname:'\u2014')))),
    h('div',{className:'card'},
      h('div',{className:'card-t'},t('service_controls')),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-sm',onClick:function(e){svcAct('restart',e.currentTarget)}},t('restart')),
        h('button',{className:'btn btn-sm btn-d',onClick:function(e){svcAct('stop',e.currentTarget)}},t('stop')),
        h('button',{className:'btn btn-sm btn-p',onClick:function(e){svcAct('start',e.currentTarget)}},t('start')))),
    renderFailoverLog());
}

function renderFailoverLog(){
  var log=S.failoverLog;var ps=10;var pages=Math.ceil(log.length/ps)||1;
  if(S.flPage>=pages)S.flPage=pages-1;if(S.flPage<0)S.flPage=0;
  var slice=log.slice(S.flPage*ps,S.flPage*ps+ps);
  return h('div',{className:'card'},
    h('div',{className:'card-t'},t('failover_log')),
    log.length===0?h('div',{style:{color:'var(--tx3)',fontSize:'12px',textAlign:'center',padding:'20px'}},t('no_failover_log')):
    h('div',null,
      h('div',{className:'tbl-wrap'},h('table',{className:'tbl'},
        h('thead',null,h('tr',null,
          h('th',null,t('uptime')),h('th',null,t('from_server')),h('th',null,t('to_server')),h('th',null,t('reason')))),
        h('tbody',null,slice.map(function(e){return h('tr',null,
          h('td',null,new Date(e.ts*1000).toLocaleString()),
          h('td',null,e.from||'\u2014'),h('td',null,e.to||'\u2014'),h('td',null,e.reason||''))})))),
      pages>1?h('div',{style:{display:'flex',justifyContent:'center',gap:'8px',marginTop:'10px'}},
        h('button',{className:'btn btn-xs',disabled:S.flPage===0,onClick:function(){S.flPage--;R()}},t('prev')),
        h('span',{style:{fontSize:'11px',color:'var(--tx3)',lineHeight:'26px'}},t('page')+' '+(S.flPage+1)+'/'+pages),
        h('button',{className:'btn btn-xs',disabled:S.flPage>=pages-1,onClick:function(){S.flPage++;R()}},t('next'))):null));
}

function renderSettings(){
  var cfg=S.settings;
  var hci,afe,aft,vpm,kse,dnsi,exci,mtui;
  return h('div',null,
    h('div',{className:'card'},
      h('div',{className:'card-t'},t('settings')),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},
          h('label',{className:'fl'},t('health_check')+' '+t('interval')+' (s)'),
          hci=h('input',{className:'input input-m',type:'number',min:'10',max:'300',value:cfg.health_check_interval||60})),
        h('div',{className:'fg'},
          h('label',{className:'fl'},t('auto_failover')),
          h('div',{style:{display:'flex',alignItems:'center',gap:'10px'}},
            afe=h('label',{className:'toggle'},h('input',{type:'checkbox',checked:cfg.auto_failover!==false}),h('span',{className:'slider'})),
            h('span',{style:{fontSize:'11px',color:'var(--tx3)'}},t('threshold')+':'),
            aft=h('input',{className:'input input-m',type:'number',min:'1',max:'10',value:cfg.failover_threshold||3,style:{width:'60px'}}),
            h('span',{style:{fontSize:'10px',color:'var(--tx3)'}},t('failures'))))),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},
          h('label',{className:'fl'},t('vpn_mode')),
          vpm=h('select',{className:'input',value:cfg.vpn_mode||'general'},
            h('option',{value:'general'},t('general')),
            h('option',{value:'selective'},t('selective')))),
        h('div',{className:'fg'},
          h('label',{className:'fl'},t('killswitch')),
          kse=h('label',{className:'toggle',style:{marginTop:'8px'}},h('input',{type:'checkbox',checked:!!cfg.kill_switch}),h('span',{className:'slider'})))),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},
          h('label',{className:'fl'},t('dns')),
          dnsi=h('input',{className:'input input-m',value:cfg.dns_upstreams||'',placeholder:'8.8.8.8, 1.1.1.1'})),
        h('div',{className:'fg'},
          h('label',{className:'fl'},t('mtu')),
          mtui=h('input',{className:'input input-m',type:'number',value:cfg.mtu||1400}))),
      h('div',{className:'fg'},
        h('label',{className:'fl'},t('exclusions_label')),
        exci=h('textarea',{className:'input input-m',value:cfg.exclusions||''})),
      h('button',{className:'btn btn-p',onClick:function(){
        saveSettings({
          health_check_interval:parseInt(hci.value)||60,
          auto_failover:afe.querySelector('input').checked,
          failover_threshold:parseInt(aft.value)||3,
          vpn_mode:vpm.value,
          kill_switch:kse.querySelector('input').checked,
          dns_upstreams:dnsi.value,
          mtu:parseInt(mtui.value)||1400,
          exclusions:exci.value
        })}},t('save'))),
    h('div',{className:'card'},
      h('div',{className:'card-t'},t('change_password')),
      (function(){var pi=h('input',{className:'input',type:'password',placeholder:t('new_password'),style:{maxWidth:'300px'}});
        return h('div',{className:'bg'},pi,
          h('button',{className:'btn btn-p btn-sm',onClick:function(e){if(pi.value.length<6){toast('Min 6 chars',true);return}chgAdmin(pi.value,e.currentTarget)}},t('save')))})()));
}

var _refreshTimer=null;
function startRefresh(){clearInterval(_refreshTimer);_refreshTimer=setInterval(function(){if(S.auth&&(S.tab==='servers'||S.tab==='monitor')){loadStatus().then(R)}},15000)}

document.addEventListener('keydown',function(e){if(e.key==='Escape'&&S.modal){S.modal=null;R()}});
applyTheme();checkAuth().then(function(){if(S.auth)loadAll()});startRefresh();
</script>
</body>
</html>
'''
