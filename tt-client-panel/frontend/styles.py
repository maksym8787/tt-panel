STYLES = r'''*{margin:0;padding:0;box-sizing:border-box}
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
  --f:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;--m:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace;
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
.periods{display:flex;gap:2px;background:var(--bg);border-radius:7px;padding:2px;border:1px solid var(--bd)}
.per{padding:4px 10px;border-radius:5px;border:none;background:transparent;color:var(--tx3);cursor:pointer;font-size:10px;font-weight:600;font-family:var(--m);transition:.15s}
.per:hover{color:var(--tx2)}.per.on{background:var(--sf2);color:var(--ac);box-shadow:0 1px 4px rgba(0,0,0,.3)}
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
.chart-wrap{position:relative;height:200px}
@media(max-width:640px){.chart-wrap{height:160px}}'''
