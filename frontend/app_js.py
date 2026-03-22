PREAMBLE_JS = r'''
var LOGO_ICON='/static/favicon.png';
var LOGO_FULL='/static/logo-full.png';
var A='/api';
'''

APP_JS = r'''
function t(k){return (T[S.lang]||T.en)[k]||T.en[k]||k}
function setLang(l){S.lang=l;localStorage.setItem('tt_lang',l);R()}
function setTheme(th){S.theme=th;localStorage.setItem('tt_theme',th);applyTheme()}
function applyTheme(){document.documentElement.setAttribute('data-theme',S.theme)}
var S={auth:false,setup:false,loading:true,tab:'dashboard',status:null,users:[],logs:null,settings:{},
  history:null,traffic:null,conns:null,online:null,summary:null,toast:null,modal:null,dbSize:null,
  connTimeline:null,activeIps:{},monPeriod:24,connPeriod:24,pendingReload:false,userFilter:'',userSort:'name_asc',monLoading:false,logsLoading:false,
  lang:localStorage.getItem('tt_lang')||'en',theme:localStorage.getItem('tt_theme')||'system',
  restartHistory:null,userNotes:{},panelSettings:null,lastActivity:Date.now()};

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
async function _loadDash(){try{var p=await Promise.all([api('/status'),api('/users')]);S.status=p[0];S.users=p[1].users}catch(e){toast(e.message,true)}await _loadActiveIps();api('/restart-history').then(function(d){S.restartHistory=d.history}).catch(function(){});api('/user-notes').then(function(d){S.userNotes=d.notes;R()}).catch(function(){});api('/panel-settings').then(function(d){S.panelSettings=d.settings}).catch(function(){})}
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
async function addUser(u,p,note){try{var r=await api('/users',{method:'POST',body:JSON.stringify({username:u,password:p})});if(note){await api('/users/'+u+'/note',{method:'PUT',body:JSON.stringify({note:note})});S.userNotes[u]=note}toast(t('user_created')+' "'+u+'" ('+t('pass_label')+': '+r.password+')');S.modal=null;loadDash()}catch(e){toast(e.message,true)}}
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
function isDarkMode(){return getComputedStyle(document.documentElement).getPropertyValue('--bg').trim().startsWith('#0')}
var chartTheme=function(){var dk=isDarkMode();return{grid:dk?'rgba(255,255,255,.06)':'rgba(0,0,0,.08)',tick:dk?'rgba(255,255,255,.5)':'rgba(0,0,0,.5)',legend:dk?'#c8d0da':'#374151',tipBg:dk?'#131a24':'#ffffff',tipBorder:dk?'#1e2a3a':'#d0d5dd',tipTitle:dk?'#e2e8f0':'#1a1a2e',tipBody:dk?'#8899aa':'#4a5568'}};
var chartOpts=function(yCallback){var ct=chartTheme();return{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,labels:{color:ct.legend,font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:ct.tipBg,borderColor:ct.tipBorder,borderWidth:1,titleColor:ct.tipTitle,bodyColor:ct.tipBody,titleFont:{family:'DM Sans',size:12,weight:600},bodyFont:{family:'JetBrains Mono',size:11},padding:10,cornerRadius:8,displayColors:true,boxWidth:8,boxHeight:8,boxPadding:4}},scales:{x:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:8,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},callback:yCallback||undefined,maxTicksLimit:5},grid:{color:ct.grid,drawBorder:false},border:{display:false}}}}};
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
  if(c1){updateChart('sess',c1,{type:'line',data:{labels:labels,datasets:[mkDataset(t('active_sessions'),d.map(function(x){return x.sessions}),chartColors.sessions)]},options:chartOpts()})}


  var c3=document.getElementById('ch-resources');
  if(c3){
    var ct=chartTheme();
    var cpuPct=d.map(function(x,i){if(i===0)return 0;var dt=x.ts-d[i-1].ts;if(dt<=0)return 0;return Math.min(100,((x.cpu-d[i-1].cpu)/dt)*100)});
    updateChart('res',c3,{type:'line',data:{labels:labels,datasets:[
      {label:t('mem_cpu').split('/')[0].trim()+' MB',data:d.map(function(x){return x.mem/1048576}),borderColor:chartColors.memory.border,backgroundColor:chartColors.memory.bg,fill:true,tension:.35,pointRadius:0,borderWidth:1.5,yAxisID:'y'},
      {label:'CPU %',data:cpuPct,borderColor:chartColors.cpu.border,backgroundColor:'transparent',fill:false,tension:.35,pointRadius:0,borderWidth:1.5,yAxisID:'y1'}
    ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,labels:{color:ct.legend,font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:ct.tipBg,borderColor:ct.tipBorder,borderWidth:1,titleColor:ct.tipTitle,bodyColor:ct.tipBody,padding:10,cornerRadius:8}},scales:{x:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:8,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,position:'left',title:{display:true,text:t('mem_cpu').split('/')[0].trim()+' MB',color:ct.tick,font:{size:9}},ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{color:ct.grid},border:{display:false}},y1:{display:true,position:'right',title:{display:true,text:'CPU %',color:ct.tick,font:{size:9}},ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{display:false},border:{display:false},min:0}}}})}
}

function drawTrafficChart(){
  if(!window.Chart){setTimeout(drawTrafficChart,500);return}
  if(!S.traffic||!S.traffic.hourly.length)return;
  var d=S.traffic.hourly;var c=document.getElementById('ch-traffic');
  if(c){
    var ct=chartTheme();
    var labels=d.map(function(x){return ts2t(x.ts)});
    updateChart('traffic',c,{type:'bar',data:{labels:labels,datasets:[{label:t('download'),data:d.map(function(x){return x.out}),backgroundColor:'rgba(34,197,94,0.5)',borderRadius:3},{label:t('upload'),data:d.map(function(x){return x['in']}),backgroundColor:'rgba(245,158,11,0.5)',borderRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,labels:{color:ct.legend,font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:ct.tipBg,borderColor:ct.tipBorder,borderWidth:1,titleColor:ct.tipTitle,bodyColor:ct.tipBody,padding:10,cornerRadius:8,callbacks:{label:function(ctx){return ctx.dataset.label+': '+fmtTooltip(ctx.raw)}}}},scales:{x:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:8},maxTicksLimit:24,maxRotation:0},stacked:true,grid:{display:false},border:{display:false}},y:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},callback:function(v){return fmtShort(v)},maxTicksLimit:5},grid:{color:ct.grid},stacked:true,border:{display:false}}}}})
  }
}

function drawConnChart(){
  if(!window.Chart)return;
  if(!S.connTimeline||!S.connTimeline.timeline.length)return;
  var d=S.connTimeline.timeline;var c=document.getElementById('ch-conns');
  if(c){
    var ct=chartTheme();
    var connColor={border:'#a78bfa',bg:'rgba(167,139,250,0.3)'};
    var ipColor={border:'#06b6d4',bg:'rgba(6,182,212,0.3)'};
    updateChart('conns',c,{type:'bar',data:{
      labels:d.map(function(x){return ts2t(x.ts)}),
      datasets:[
        {label:t('connections'),data:d.map(function(x){return x.connections}),backgroundColor:connColor.bg,borderColor:connColor.border,borderWidth:1,borderRadius:3,order:2},
        {label:t('unique_ips_label'),data:d.map(function(x){return x.unique_ips}),type:'line',borderColor:ipColor.border,backgroundColor:'transparent',borderWidth:2,tension:.35,pointRadius:2,pointBackgroundColor:ipColor.border,order:1,yAxisID:'y1'}
      ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,labels:{color:ct.legend,font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:ct.tipBg,borderColor:ct.tipBorder,borderWidth:1,titleColor:ct.tipTitle,bodyColor:ct.tipBody,padding:10,cornerRadius:8}},scales:{x:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:8,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,position:'left',title:{display:true,text:t('connections'),color:ct.tick,font:{size:9}},ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{color:ct.grid},border:{display:false}},y1:{display:true,position:'right',title:{display:true,text:t('unique_ips_label'),color:ct.tick,font:{size:9}},ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{display:false},border:{display:false},min:0}}}})
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
  var gradColor=pct>80?'var(--rd)':pct>50?'var(--or)':'var(--gn)';
  return h('div',{className:'stat'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'baseline'}},
      h('div',{className:'stat-l'},label),
      h('div',{style:{fontSize:'16px',fontWeight:'700',fontFamily:'var(--m)',color:gradColor}},String(pct)+unit)),
    h('div',{className:'progress-bar'},
      h('div',{className:'progress-fill',style:{width:pct+'%',background:gradColor}})),
    sub?h('div',{className:'stat-sub',style:{marginTop:'4px'}},sub):null)
}

function renderDash(){
  var s=S.status;if(!s){loadAll();return h('div',{className:'tab-content'},h('div',{className:'skeleton skel-card'}),h('div',{className:'skeleton skel-card'}),h('div',{className:'skeleton skel-card'}))}
  var l=s.live||{};var cert=s.certificate;var sm=S.summary;
  var certDays=cert?cert.days:null;var certClass=certDays!=null?(certDays<14?'off':certDays<30?'warn':'on'):'';

  var alerts=[];
  if(s.service&&!s.service.active) alerts.push({cls:'alert-danger',msg:t('alert_service_down')});
  if(cert&&cert.days!=null&&cert.days<7) alerts.push({cls:'alert-warn',msg:t('alert_cert_expiring').replace('{days}',cert.days)});
  if(s.vps&&s.vps.disk_pct>90) alerts.push({cls:'alert-danger',msg:t('alert_disk_full')});

  return h('div',{className:'tab-content'},
    alerts.map(function(a){return h('div',{className:'alert-bar '+a.cls},'\u26A0 ',a.msg)}),
    h('div',{className:'grid grid5 section-gap'},
      h('div',{className:'stat '+(s.service&&s.service.active?'stat-green':'stat-red')},
        h('div',{className:'stat-l'},t('service')),
        h('div',{className:'stat-v count-up '+(s.service&&s.service.active?'on':'off')},s.service&&s.service.active?t('online'):t('offline')),
        s.service&&s.service.active?h('div',{className:'stat-sub'},h('span',{className:'dot dot-on pulse'}),t('running')):null),
      h('div',{className:'stat stat-cyan'},
        h('div',{className:'stat-l'},t('tcp_sessions')),
        h('div',{className:'stat-v count-up ac'},String(l.sessions||0)),
        h('div',{className:'stat-sub'},String(s.users_count||0)+' '+t('users_configured'))),
      h('div',{className:'stat'},
        h('div',{className:'stat-l'},t('sockets')),
        h('div',{className:'stat-v count-up'},(l.tcp_sockets||0)+' / '+(l.udp_sockets||0)),
        h('div',{className:'stat-sub'},'FDs: '+(l.open_fds||0))),
      h('div',{className:'stat'},
        h('div',{className:'stat-l'},t('mem_cpu')),
        h('div',{className:'stat-v count-up'},(l.memory_mb||0)+' MB'),
        h('div',{className:'stat-sub'},'CPU: '+(l.cpu_seconds||0)+'s total')),
      h('div',{className:'stat '+(certDays!=null&&certDays<14?'stat-red':certDays!=null&&certDays<30?'stat-orange':'')},
        h('div',{className:'stat-l'},t('certificate')),
        h('div',{className:'stat-v count-up '+certClass},certDays!=null?certDays+'d':'\u2014'),
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

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('controls')),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-sm btn-p',onClick:function(){S.modal={t:'add'};R()}},'\u2795 '+t('add_user')),
        h('button',{className:'btn btn-sm',onClick:function(e){svcAct('restart',e.currentTarget)}},t('restart')),
        h('button',{className:'btn btn-sm',onClick:function(e){svcAct('reload',e.currentTarget)}},t('reload_tls')),
        h('button',{className:'btn btn-sm btn-d',onClick:function(e){svcAct('stop',e.currentTarget)}},t('stop')),
        h('button',{className:'btn btn-sm',onClick:renewCert},t('renew_cert')))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('server_info')),
      h('div',{style:{fontFamily:'var(--m)',fontSize:'11px',color:'var(--tx3)',lineHeight:'1.8',whiteSpace:'pre-wrap'}},
        t('domain')+':          '+s.domain+'\nIP:              '+s.ip+'\nPID:             '+(s.service&&s.service.pid?s.service.pid:'\u2014')+'\n'+t('server_uptime')+':  '+fmtUptime(s.vps&&s.vps.uptime_seconds)+'\n'+t('service_uptime')+': '+(s.service&&s.service.uptime_seconds?new Date(Date.now()-s.service.uptime_seconds*1000).toLocaleString():'\u2014'))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('restart_history')),
      S.restartHistory&&S.restartHistory.length?h('div',{className:'tbl-wrap'},
        h('table',{className:'tbl'},
          h('thead',null,h('tr',null,h('th',null,t('restart_time')),h('th',null,t('restart_reason')))),
          h('tbody',null,S.restartHistory.map(function(r){var reasonKey='reason_'+r.reason;return h('tr',null,
            h('td',null,r.time?new Date(r.time*1000).toLocaleString():'\u2014'),
            h('td',null,t(reasonKey)!==reasonKey?t(reasonKey):r.reason))})))):
        h('div',{style:{color:'var(--tx3)',fontSize:'12px',textAlign:'center',padding:'12px 0'}},t('no_restart_history')))
  );
}

// ─── Monitor ────────────────────────────────────────────
function renderMonitor(){
  var periods=[{v:1,l:'1h'},{v:6,l:'6h'},{v:24,l:'24h'},{v:168,l:'7d'}];

  if(S.monLoading&&!S.history){return h('div',{className:'tab-content'},h('div',{className:'skeleton skel-chart'}),h('div',{className:'skeleton skel-chart'}),h('div',{className:'skeleton skel-chart'}))}

  return h('div',{className:'tab-content'},
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
  return h('div',{className:'tab-content'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'16px',gap:'12px',flexWrap:'wrap'}},
      h('div',{style:{fontSize:'13px',fontWeight:'600'}},S.users.length+' '+(S.users.length!==1?t('users_pl'):t('user'))),
      h('div',{className:'bg',style:{flex:'1',justifyContent:'flex-end'}},
        h('select',{className:'input',style:{maxWidth:'160px',padding:'6px 8px',fontSize:'11px'},value:S.userSort,onChange:function(e){S.userSort=e.target.value;R()}},sortOpts.map(function(o){return h('option',{value:o.v},o.l)})),
        h('input',{className:'input',placeholder:t('search_users'),style:{maxWidth:'200px',padding:'6px 12px',fontSize:'12px'},id:'user-search',value:S.userFilter||'',onInput:function(e){S.userFilter=e.target.value;R()}}),
        h('button',{className:'btn btn-p btn-sm',onClick:function(){S.modal={t:'add'};R()}},t('add_user')),
        h('button',{className:'btn btn-sm',onClick:function(){window.location.href=A+'/users/export'}},t('export_csv')),
        h('button',{className:'btn btn-sm',onClick:function(){var inp=document.createElement('input');inp.type='file';inp.accept='.csv';inp.onchange=function(){if(!inp.files[0])return;var rd=new FileReader();rd.onload=function(){api('/users/import',{method:'POST',body:JSON.stringify({csv:rd.result})}).then(function(d){toast(t('import_success').replace('{count}',d.count||0));loadDash()}).catch(function(e){toast(t('import_error')+': '+e.message,true)})};rd.readAsText(inp.files[0])};inp.click()}},t('import_csv')))),
    aipCount?h('div',{className:'card',style:{marginBottom:'14px'}},
      h('div',{className:'card-t'},h('span',null,aipCount+' '+(aipCount!==1?t('active_ips'):t('active_ip')))),
      h('div',{style:{display:'flex',flexWrap:'wrap',gap:'8px'}},aips.map(function(ip){
        var info=S.activeIps[ip];
        return h('div',{className:'badge b-gn',style:{fontSize:'11px',padding:'4px 10px'}},
          h('span',{className:'dot dot-on',style:{width:'6px',height:'6px'}}),ip+' ('+info.connections+' '+t('conn')+', '+ago(info.last_seen)+')')}))):null,
    h('div',{id:'user-list'},filtered.map(function(u){return renderUserCard(u)})));
}
function renderUserCard(u){var dis=u.enabled===false;var created=u.created_at?u.created_at.replace('T',' ').substring(0,16):'';var uNote=S.userNotes[u.username];
  return h('div',{className:'uc'+(dis?' uc-dis':'')},
  h('div',{className:'ui'},
    h('div',{className:'ua'+(dis?' ua-dis':'')},u.username[0].toUpperCase()),
    h('div',null,
      h('div',{style:{display:'flex',alignItems:'center',gap:'6px'}},
        h('span',{className:'un'+(dis?' un-dis':'')},u.username),
        dis?h('span',{className:'badge b-rd',style:{fontSize:'9px'}},t('user_disabled')):null),
      created?h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginTop:'1px'}},t('created_label')+': '+created):null,
      h('div',{style:{display:'flex',alignItems:'center',gap:'4px',marginTop:'2px'}},
        uNote?h('span',{style:{fontSize:'10px',color:'var(--tx2)',fontStyle:'italic'}},uNote):null,
        h('span',{style:{cursor:'pointer',fontSize:'11px',color:'var(--tx3)'},title:t('note'),onClick:function(){var txt=prompt(t('note_placeholder'),uNote||'');if(txt!==null){api('/users/'+u.username+'/note',{method:'PUT',body:JSON.stringify({note:txt})}).then(function(){S.userNotes[u.username]=txt||undefined;if(!txt)delete S.userNotes[u.username];toast(t('note_saved'));R()}).catch(function(e){toast(e.message,true)})}}},'\u270F\uFE0F')),
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
  var s=S.settings;if(!s.vpn_toml&&s.vpn_toml!==''){loadSettings();return h('div',{className:'tab-content'},h('div',{className:'skeleton skel-card'}),h('div',{className:'skeleton skel-card'}))}
  var va,ra;var ps=S.panelSettings||{};
  var ttlOpts=[{v:300,l:'5 '+t('minutes')},{v:900,l:'15 '+t('minutes')},{v:1800,l:'30 '+t('minutes')},{v:3600,l:'1h'},{v:14400,l:'4h'},{v:43200,l:'12h'},{v:86400,l:'24h'}];
  var renewOn=ps.auto_renew_enabled!==false;
  return h('div',{className:'tab-content'},
    h('div',{className:'card'},
      h('div',{className:'card-t'},t('settings')),
      h('div',{style:{display:'flex',gap:'16px',flexWrap:'wrap',alignItems:'flex-end'}},
        h('div',{style:{flex:'1',minWidth:'160px'}},
          h('div',{className:'fl'},t('session_timeout')),
          h('select',{className:'input',style:{maxWidth:'180px'},value:String(ps.session_ttl||86400),onChange:function(e){var val=parseInt(e.target.value);api('/panel-settings',{method:'PUT',body:JSON.stringify({session_ttl:val})}).then(function(){if(!S.panelSettings)S.panelSettings={};S.panelSettings.session_ttl=val;toast(t('saved'))}).catch(function(er){toast(er.message,true)})}},ttlOpts.map(function(o){return h('option',{value:String(o.v),selected:o.v===(ps.session_ttl||86400)},o.l)}))),
        h('div',{style:{flex:'1',minWidth:'160px'}},
          h('div',{className:'fl'},t('cert_auto_renew')),
          h('button',{className:'btn btn-sm'+(renewOn?' btn-d':' btn-p'),style:{minWidth:'100px'},onClick:function(){var nv=!renewOn;api('/panel-settings',{method:'PUT',body:JSON.stringify({auto_renew_enabled:nv})}).then(function(){if(!S.panelSettings)S.panelSettings={};S.panelSettings.auto_renew_enabled=nv;toast(t('saved'));R()}).catch(function(er){toast(er.message,true)})}},renewOn?t('btn_disable'):t('btn_enable'))),
        h('div',{style:{flex:'0',minWidth:'120px'}},
          h('div',{className:'fl'},t('cert_renew_days')),
          h('input',{className:'input',type:'number',min:'1',max:'60',style:{maxWidth:'80px'},value:String(ps.auto_renew_days||10),onChange:function(e){var val=parseInt(e.target.value);if(val<1||val>60)return;api('/panel-settings',{method:'PUT',body:JSON.stringify({auto_renew_days:val})}).then(function(){if(!S.panelSettings)S.panelSettings={};S.panelSettings.auto_renew_days=val;toast(t('saved'))}).catch(function(er){toast(er.message,true)})}})))),
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
  return h('div',{className:'tab-content'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'12px'}},
      h('div',{style:{fontSize:'13px',fontWeight:'600'}},t('service_logs')),
      h('button',{className:'btn btn-sm',onClick:loadLogs},t('refresh'))),
    S.logsLoading?h('div',null,h('div',{className:'skeleton skel-row'}),h('div',{className:'skeleton skel-row'}),h('div',{className:'skeleton skel-row'}),h('div',{className:'skeleton skel-row'}),h('div',{className:'skeleton skel-row'})):h('div',{className:'lb'},S.logs===null?t('click_refresh'):S.logs===''?'(empty log file)':S.logs));
}

// ─── Modal (#14 proper dialogs, #19 accessible with Escape) ─
function renderModal(){
  var m=S.modal;if(!m)return h('div');
  var close=function(){S.modal=null;R()};
  var content;
  if(m.t==='add'){
    var ni,pi,nti;
    content=h('div',{className:'md',role:'dialog','aria-modal':'true','aria-label':t('add_vpn_user')},
      h('div',{className:'md-t'},t('add_vpn_user')),
      h('div',{className:'fg'},h('label',{className:'fl'},t('username')),ni=h('input',{className:'input',placeholder:'e.g. phone-maks'})),
      h('div',{className:'fg'},h('label',{className:'fl'},t('password_empty_auto')),pi=h('input',{className:'input input-m',placeholder:'auto'})),
      h('div',{className:'fg'},h('label',{className:'fl'},t('note')),nti=h('input',{className:'input',placeholder:t('note_placeholder'),maxLength:200})),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(){addUser(ni.value,pi.value,nti.value.trim())}},t('create')),
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
document.addEventListener('click',function(){S.lastActivity=Date.now()});
document.addEventListener('keypress',function(){S.lastActivity=Date.now()});
setInterval(function(){if(S.auth&&S.panelSettings&&S.panelSettings.session_ttl){if((Date.now()-S.lastActivity)>S.panelSettings.session_ttl*1000){doLogout()}}},60000);
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
'''
