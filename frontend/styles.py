CSS = '''
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
.grid{display:grid;gap:10px}.grid2{grid-template-columns:1fr 1fr}.grid3{grid-template-columns:1fr 1fr 1fr}.grid4{grid-template-columns:repeat(4,1fr)}.grid5{grid-template-columns:repeat(5,1fr)}
@media(max-width:900px){.grid5{grid-template-columns:repeat(3,1fr)}}
@media(max-width:640px){.grid3,.grid4,.grid5{grid-template-columns:1fr 1fr}.grid2{grid-template-columns:1fr}}
@media(max-width:400px){.grid3,.grid4,.grid5{grid-template-columns:1fr}}

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
.alert-bar{padding:10px 16px;border-radius:var(--r2);margin-bottom:10px;font-size:12px;font-weight:500;display:flex;align-items:center;gap:8px}
.alert-warn{background:var(--orbg);border:1px solid rgba(245,158,11,.25);color:var(--or)}
.alert-danger{background:var(--rdbg);border:1px solid rgba(239,68,68,.25);color:var(--rd)}
@keyframes shimmer{0%{background-position:-200px 0}100%{background-position:200px 0}}
.skeleton{background:linear-gradient(90deg,var(--sf2) 25%,var(--sf3) 50%,var(--sf2) 75%);background-size:400px 100%;animation:shimmer 1.5s infinite;border-radius:var(--r2)}
.skel-card{height:120px;margin-bottom:14px}
.skel-chart{height:180px;margin-bottom:14px}
.skel-row{height:40px;margin-bottom:8px}
.tab-content{animation:tabFade .25s ease-out}
@keyframes tabFade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.progress-bar{height:6px;border-radius:3px;background:var(--sf2);overflow:hidden;margin-top:6px}
.progress-fill{height:100%;border-radius:3px;transition:width .5s ease}
.count-up{animation:countFade .4s ease-out}
@keyframes countFade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
'''
