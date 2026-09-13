PREAMBLE_JS = r'''
// BASE is injected by the server: '' when the panel is served at the root, or
// '/prefix' when it sits behind the endpoint's reverse proxy.
if(typeof BASE==='undefined')var BASE='';
var LOGO_ICON=BASE+'/static/favicon.png';
var LOGO_FULL=BASE+'/static/logo-full.png';
var A=BASE+'/api';
var POLL_DASH_MS=30000;
var POLL_MON_MS=60000;
var TOAST_MS=3500;
var REQUEST_TIMEOUT_MS=20000;
var FOCUS_DELAY_MS=50;
'''

CORE_JS = r'''
function t(k){return (T[S.lang]||T.en)[k]||T.en[k]||k}
function setLang(l){S.lang=l;localStorage.setItem('tt_lang',l);if(!S.auth){_softUpdateLogin()}else{R()}}
function setTheme(th){S.theme=th;localStorage.setItem('tt_theme',th);applyTheme();if(!S.auth){_softUpdateLogin()}else{R(function(){if(S.tab==='monitor')drawMonitorCharts()})}}
function applyTheme(){document.documentElement.setAttribute('data-theme',S.theme)}
var S={auth:false,setup:false,setupLocked:false,minPwLen:12,loading:true,tab:'dashboard',status:null,users:[],logs:null,settings:{},
  history:null,traffic:null,conns:null,online:null,summary:null,toast:null,modal:null,dbSize:null,
  connTimeline:null,perUser:null,loginSecurity:null,telegram:null,activeIps:{},monPeriod:24,connPeriod:24,pendingReload:false,userFilter:'',userSort:'name_asc',monLoading:false,logsLoading:false,dashLoading:false,structuredSettings:null,
  lang:localStorage.getItem('tt_lang')||'en',theme:localStorage.getItem('tt_theme')||'system',
  restartHistory:null,userNotes:{},panelSettings:null,lastActivity:Date.now()};

function _errMsg(d,r){
  var det=d&&d.detail;
  if(typeof det==='string')return det;
  if(Array.isArray(det)&&det.length){var f=det[0];return (f&&(f.msg||f.detail))||r.statusText||('HTTP '+r.status)}
  if(det&&typeof det==='object')return det.msg||det.detail||('HTTP '+r.status);
  return r.statusText||('HTTP '+r.status)}

function onUnauthorized(){
  if(!S.auth)return;
  S.auth=false;S.modal=null;S.status=null;S.users=[];
  stopRefreshTimers();
  toast(t('session_expired'),true);R()}

async function api(p,o){
  o=o||{};
  var ctrl=new AbortController();
  var timer=setTimeout(function(){ctrl.abort()},REQUEST_TIMEOUT_MS);
  var r;
  try{
    r=await fetch(A+p,{headers:{'Content-Type':'application/json'},credentials:'same-origin',signal:ctrl.signal,...o});
  }catch(err){
    clearTimeout(timer);
    throw new Error(err&&err.name==='AbortError'?t('request_timeout'):t('network_error'));
  }
  clearTimeout(timer);
  var d={};
  var txt='';
  try{txt=await r.text()}catch(e){txt=''}
  if(txt){try{d=JSON.parse(txt)}catch(e){d={}}}
  if(r.status===401&&p.indexOf('/auth-status')!==0&&p.indexOf('/login')!==0){onUnauthorized();throw new Error(t('session_expired'))}
  if(!r.ok)throw new Error(_errMsg(d,r));
  return d}

var _toastTimer=null;
function toast(m,e){
  S.toast={m:m,e:!!e};
  _paintToast();
  if(_toastTimer)clearTimeout(_toastTimer);
  _toastTimer=setTimeout(function(){_toastTimer=null;S.toast=null;_paintToast()},TOAST_MS)}
function _paintToast(){
  var host=document.getElementById('toast-host');
  if(!host)return;
  host.replaceChildren();
  if(S.toast)host.appendChild(h('div',{className:'toast '+(S.toast.e?'toast-err':'toast-ok')},S.toast.m))}

function fmt(b){if(b==null)return '0 B';if(b>=1099511627776)return(b/1099511627776).toFixed(2)+' TB';if(b>=1073741824)return(b/1073741824).toFixed(2)+' GB';if(b>=1048576)return(b/1048576).toFixed(1)+' MB';if(b>=1024)return(b/1024).toFixed(0)+' KB';return b+' B'}
function ts2t(ts,spanHours){
  var d=new Date(ts*1000);
  var hh=String(d.getHours()).padStart(2,'0');
  var mm=String(d.getMinutes()).padStart(2,'0');
  if(spanHours!=null&&spanHours<=2)return hh+':'+mm;
  var label=hh+':00';
  if(d.getHours()===0)return d.getDate()+'.'+(d.getMonth()+1)+' '+label;
  return label}
function ts2dt(ts){return new Date(ts*1000).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
function ago(ts){var d=Math.max(0,Math.floor(Date.now()/1000-ts));if(d<60)return d+' '+t('s_ago');if(d<3600)return Math.floor(d/60)+' '+t('m_ago');if(d<86400)return Math.floor(d/3600)+' '+t('h_ago');return Math.floor(d/86400)+' '+t('d_ago')}
function fmtUptime(sec){if(!sec)return '—';var d=Math.floor(sec/86400),h=Math.floor((sec%86400)/3600),m=Math.floor((sec%3600)/60);if(d>0)return d+'d '+h+'h '+m+'m';if(h>0)return h+'h '+m+'m';return m+'m'}
function enc(s){return encodeURIComponent(s)}

function copyText(txt){
  if(navigator.clipboard&&navigator.clipboard.writeText){
    return navigator.clipboard.writeText(txt).then(function(){toast(t('copied'))}).catch(function(){_copyFallback(txt)})}
  _copyFallback(txt);
  return Promise.resolve()}
function _copyFallback(txt){
  try{
    var ta=document.createElement('textarea');
    ta.value=txt;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.opacity='0';
    document.body.appendChild(ta);ta.select();
    var ok=document.execCommand('copy');
    document.body.removeChild(ta);
    toast(ok?t('copied'):t('copy_failed'),!ok)}
  catch(e){toast(t('copy_failed'),true)}}
function copyPassword(pw){copyText(pw)}

function withLoading(btn,fn){
  if(!btn)return Promise.resolve(fn());
  var orig=btn.textContent;btn.disabled=true;btn.textContent='…';
  return Promise.resolve(fn()).finally(function(){if(btn.isConnected){btn.disabled=false;btn.textContent=orig}})}

async function checkAuth(){
  try{var r=await api('/auth-status');S.auth=r.authenticated;S.setup=r.setup_required;S.setupLocked=!!r.setup_locked;if(r.min_password_len)S.minPwLen=r.min_password_len}
  catch(e){S.auth=false}
  S.loading=false;R();
  if(S.auth)loadAll()}
async function doLogin(pw){try{await api('/login',{method:'POST',body:JSON.stringify({password:pw})});S.auth=true;R();loadAll()}catch(e){toast(e.message,true)}}
async function doSetup(pw){
  if(!pw||pw.length<S.minPwLen){toast(t('pw_too_short').replace('{n}',S.minPwLen),true);return}
  try{await api('/setup',{method:'POST',body:JSON.stringify({password:pw})});S.setup=false;await doLogin(pw)}catch(e){toast(e.message,true)}}
async function doLogout(){
  try{await api('/logout',{method:'POST'})}
  catch(e){}
  finally{S.auth=false;S.modal=null;stopRefreshTimers();R()}}

async function loadAll(){
  if(S.dashLoading)return;
  S.dashLoading=true;
  try{await Promise.all([_loadDash(),_loadSummary(),_checkPendingReload()])}
  finally{S.dashLoading=false}
  R()}
async function loadDash(){if(S.dashLoading)return;S.dashLoading=true;try{await _loadDash()}finally{S.dashLoading=false}R()}
async function _loadDash(){
  try{var p=await Promise.all([api('/status'),api('/users')]);S.status=p[0];S.users=p[1].users;if(S.status&&S.status.domain)document.title='TTAdmin - '+S.status.domain}catch(e){toast(e.message,true)}
  await _loadActiveIps();
  api('/restart-history').then(function(d){S.restartHistory=d.history}).catch(function(){});
  api('/user-notes').then(function(d){S.userNotes=d.notes;Rbg()}).catch(function(){});
  api('/panel-settings').then(function(d){S.panelSettings=d.settings}).catch(function(){})}
async function _loadSummary(){try{S.summary=await api('/monitoring/summary')}catch(e){}}
async function _loadHistory(h){if(h!=null)S.monPeriod=h;try{S.history=await api('/monitoring/history?hours='+S.monPeriod)}catch(e){toast(e.message,true)}}
async function _loadConns(h){if(h!=null)S.connPeriod=h;try{S.conns=await api('/monitoring/connections?hours='+S.connPeriod)}catch(e){toast(e.message,true)}}
async function _loadConnTimeline(){try{S.connTimeline=await api('/monitoring/conn-timeline?hours='+S.monPeriod)}catch(e){}}
async function _loadOnline(){try{S.online=await api('/monitoring/online')}catch(e){}}
async function _loadDbSize(){try{S.dbSize=await api('/monitoring/db-size')}catch(e){}}
async function _loadLoginSecurity(){try{S.loginSecurity=await api('/security/logins');R()}catch(e){}}
async function _loadPerUser(){try{S.perUser=await api('/monitoring/per-user?hours='+S.monPeriod)}catch(e){}}
async function _loadActiveIps(){try{var r=await api('/active-ips');S.activeIps=r.active_ips||{}}catch(e){}}
async function _checkPendingReload(){try{var r=await api('/pending-reload');S.pendingReload=r.pending}catch(e){}}
async function loadHistory(h){await Promise.all([_loadHistory(h),_loadTraffic(),_loadConnTimeline()]);R(drawMonitorCharts)}
async function _loadTraffic(h){try{var hours=h||S.monPeriod||24;S.traffic=await api('/monitoring/traffic?hours='+hours)}catch(e){}}
async function loadLogs(){S.logsLoading=true;R();try{var r=await api('/logs?lines=200');S.logs=r.logs||''}catch(e){S.logs='Error: '+e.message;toast(e.message,true)}S.logsLoading=false;R()}
async function loadSettings(){
  if(S.settingsLoading)return;
  S.settingsLoading=true;
  try{S.settings=await api('/settings')}catch(e){toast(e.message,true)}
  try{S.structuredSettings=await api('/settings/structured')}catch(e){}
  try{S.loginSecurity=await api('/security/logins')}catch(e){}
  try{S.telegram=(await api('/telegram')).telegram}catch(e){}
  S.settingsLoading=false;R()}
async function loadMonitorAll(){
  S.monLoading=true;R();
  await Promise.all([_loadHistory(),_loadTraffic(),_loadConnTimeline(),_loadOnline(),_loadConns(),_loadDbSize(),_loadPerUser()]);
  S.monLoading=false;R(drawMonitorCharts)}
function drawMonitorCharts(){if(!window.Chart)return;drawAllCharts();drawTrafficChart();drawConnChart()}

async function toggleUser(u,btn){await withLoading(btn,async function(){try{var r=await api('/users/'+enc(u)+'/toggle',{method:'PUT'});var user=S.users.find(function(x){return x.username===u});if(user)user.enabled=r.enabled;toast(r.enabled?t('user_enabled'):t('user_disabled'));R()}catch(e){toast(e.message,true)}})}
async function addUser(u,p,note,btn){
  if(!u||!u.trim()){toast(t('username')+': '+t('required'),true);return}
  await withLoading(btn,async function(){
    var r;
    try{r=await api('/users',{method:'POST',body:JSON.stringify({username:u.trim(),password:p})})}
    catch(e){toast(e.message,true);return}
    S.modal=null;
    toast(t('user_created')+' "'+r.username+'" ('+t('pass_label')+': '+r.password+')');
    if(note){
      try{await api('/users/'+enc(r.username)+'/note',{method:'PUT',body:JSON.stringify({note:note})});S.userNotes[r.username]=note}
      catch(e){toast(t('note_save_failed')+': '+e.message,true)}}
    loadDash()})}
async function deleteUser(u){S.modal={t:'confirm',title:t('delete_user'),msg:t('delete_confirm')+' "'+u+'"?',onConfirm:async function(btn){await withLoading(btn,async function(){try{await api('/users/'+enc(u),{method:'DELETE'});toast(t('deleted'));S.modal=null;loadDash()}catch(e){toast(e.message,true)}})}};R()}
async function chgPass(u){S.modal={t:'chgpass',u:u};R()}
async function doChgPass(u,p,btn){if(!p){toast(t('password')+': '+t('required'),true);return}await withLoading(btn,async function(){try{await api('/users/'+enc(u),{method:'PUT',body:JSON.stringify({password:p})});toast(t('changed'));S.modal=null;loadDash()}catch(e){toast(e.message,true)}})}
async function showCfg(u,f){try{var r=await api('/users/'+enc(u)+'/config?fmt='+enc(f));S.modal={t:'cfg',u:u,c:r.config,f:f};R()}catch(e){toast(e.message,true)}}
function paintQr(){
  var el=document.getElementById('qr-t');
  if(!el||!S.modal||S.modal.t!=='cfg'||S.modal.f!=='deeplink')return;
  el.replaceChildren();
  if(window.QRCode){new QRCode(el,{text:S.modal.c,width:200,height:200,correctLevel:QRCode.CorrectLevel.M})}
  else{el.textContent=t('qr_not_loaded')}}
async function svcAct(a,btn){
  await withLoading(btn,async function(){
    try{
      var r=await api('/service/'+enc(a),{method:'POST'});
      if(r&&r.ok===false)throw new Error(r.output||t('svc_action_failed'));
      toast(t('service')+' '+a+' '+t('svc_action_ok'));
      setTimeout(loadDash,2000)}
    catch(e){toast(e.message,true)}})}
function confirmSvcAct(a,btn){
  if(a==='restart'||a==='stop'){
    S.modal={t:'confirm',title:t('service')+': '+a,msg:t('svc_confirm_'+a),onConfirm:function(b){S.modal=null;R();svcAct(a,b)}};R();return}
  svcAct(a,btn)}
async function saveCfg(f,c,btn){await withLoading(btn,async function(){try{await api('/settings/'+enc(f),{method:'PUT',body:JSON.stringify({content:c})});toast(t('saved'));await loadSettings();_checkPendingReload().then(R)}catch(e){toast(e.message,true)}})}
async function renewCert(){S.modal={t:'confirm',title:t('renew_cert'),msg:t('renew_confirm'),onConfirm:async function(btn){await withLoading(btn,async function(){try{var r=await api('/cert/renew',{method:'POST'});S.modal=null;toast(r.message,!r.ok);setTimeout(loadAll,3000)}catch(e){S.modal=null;toast(e.message,true)}})}};R()}
async function chgAdmin(){S.modal={t:'chgadmin'};R()}
async function doChgAdmin(cur,p,btn){
  if(!cur){toast(t('current_password')+': '+t('required'),true);return}
  if(!p||p.length<S.minPwLen){toast(t('pw_too_short').replace('{n}',S.minPwLen),true);return}
  await withLoading(btn,async function(){
    try{
      await api('/change-password',{method:'POST',body:JSON.stringify({current_password:cur,password:p})});
      S.modal=null;S.auth=false;stopRefreshTimers();
      toast(t('changed_relogin'));R()}
    catch(e){toast(e.message,true)}})}
async function applyReload(btn){await withLoading(btn,async function(){try{await api('/apply-reload',{method:'POST'});toast(t('service')+' '+t('restart').toLowerCase());S.pendingReload=false;R();setTimeout(loadDash,2000)}catch(e){toast(e.message,true)}})}

// Handlers live in el.__h and are invoked through one stable dispatcher per
// event type. Re-rendering then only swaps the function in __h — no listener
// churn, and a patched node never keeps a stale closure.
function _bindHandler(e,type,fn){
  e.__h=e.__h||{};
  var had=(e.__h[type]!==undefined);
  e.__h[type]=fn;
  if(!had){
    e.addEventListener(type,function(ev){
      var f=e.__h&&e.__h[type];
      if(f)return f.call(e,ev);
    });
  }
}

var _PROPS={checked:1,selected:1,disabled:1};

function h(t,a){
  var e=document.createElement(t);
  e.__a=a||{};
  var deferValue=null;
  if(a){
    var keys=Object.keys(a);
    for(var ki=0;ki<keys.length;ki++){
      var k=keys[ki],v=a[k];
      if(k==='style'&&typeof v==='object')Object.assign(e.style,v);
      else if(k.substr(0,2)==='on')_bindHandler(e,k.slice(2).toLowerCase(),v);
      else if(k==='className')e.className=v;
      else if(k==='value'){deferValue=v}
      else if(_PROPS[k]){if(v!==false&&v!=null)e[k]=v}
      else e.setAttribute(k,v);
    }
  }
  for(var i=2;i<arguments.length;i++){
    var x=arguments[i];
    if(Array.isArray(x)){for(var j=0;j<x.length;j++)appendNode(e,x[j])}
    else{appendNode(e,x)}
  }
  if(deferValue!==null){e.value=deferValue;e.__val=deferValue}
  return e}

function appendNode(e,x){if(x==null||x===false||x===undefined)return;if(typeof x==='number')x=String(x);if(typeof x==='string')e.appendChild(document.createTextNode(x));else if(x.nodeType)e.appendChild(x);else if(Array.isArray(x)){for(var i=0;i<x.length;i++)appendNode(e,x[i])}}

// ─── Incremental DOM update ──────────────────────────────
// Replacing the whole tree on every tick is what made the panel look like it
// reloaded: it wiped typed text, focus, selection, hover state and forced
// Chart.js to rebuild every canvas. Patching touches only what changed.
function _sameNode(a,b){
  if(a.nodeType!==b.nodeType)return false;
  if(a.nodeType===3)return true;
  if(a.nodeName!==b.nodeName)return false;
  // an explicit id is treated as identity, so slots never get swapped
  if(a.id||b.id)return a.id===b.id;
  return true}

function _patchAttrs(oldEl,newEl){
  var oa=oldEl.__a||{}, na=newEl.__a||{};
  // styles set inline by h()
  if(na.style&&typeof na.style==='object'){
    var sk=Object.keys(na.style);
    for(var i=0;i<sk.length;i++){
      if(oldEl.style[sk[i]]!==newEl.style[sk[i]])oldEl.style[sk[i]]=newEl.style[sk[i]];
    }
  }
  if(oldEl.className!==newEl.className)oldEl.className=newEl.className;
  // attributes present on the new node
  var na2=newEl.attributes;
  for(var j=0;j<na2.length;j++){
    var at=na2[j];
    if(at.name==='style'||at.name==='class')continue;
    if(oldEl.getAttribute(at.name)!==at.value)oldEl.setAttribute(at.name,at.value);
  }
  // attributes that disappeared
  var oa2=oldEl.attributes;
  for(var k=oa2.length-1;k>=0;k--){
    var an=oa2[k].name;
    if(an==='style'||an==='class')continue;
    if(!newEl.hasAttribute(an))oldEl.removeAttribute(an);
  }
  // real properties
  var pk=Object.keys(_PROPS);
  for(var p=0;p<pk.length;p++){
    var name=pk[p];
    if(name in na || name in oa){
      var want=(name in na)?(na[name]===false||na[name]==null?false:na[name]):false;
      if(oldEl[name]!==want)oldEl[name]=want;
    }
  }
  // swap handlers in place — the dispatcher stays attached
  if(newEl.__h){
    var hk=Object.keys(newEl.__h);
    for(var hi=0;hi<hk.length;hi++)_bindHandler(oldEl,hk[hi],newEl.__h[hk[hi]]);
  }
  if(oldEl.__h){
    var ok=Object.keys(oldEl.__h);
    for(var oi=0;oi<ok.length;oi++){
      if(!newEl.__h||newEl.__h[ok[oi]]===undefined)oldEl.__h[ok[oi]]=null;
    }
  }
  // never fight the user for the field they are typing in
  if(newEl.__val!==undefined&&document.activeElement!==oldEl&&oldEl.value!==newEl.__val){
    oldEl.value=newEl.__val;
  }
  oldEl.__a=na;
}

function _patch(parent,oldNode,newNode){
  if(!oldNode&&!newNode)return;
  if(!oldNode){parent.appendChild(newNode);return}
  if(!newNode){parent.removeChild(oldNode);return}
  if(!_sameNode(oldNode,newNode)){parent.replaceChild(newNode,oldNode);return}
  if(oldNode.nodeType===3){
    if(oldNode.nodeValue!==newNode.nodeValue)oldNode.nodeValue=newNode.nodeValue;
    return;
  }
  if(oldNode.nodeType!==1)return;
  // a canvas keeps its Chart.js instance only if we leave the element alone
  if(oldNode.nodeName==='CANVAS'){_patchAttrs(oldNode,newNode);return}
  _patchAttrs(oldNode,newNode);
  var oldKids=[],newKids=[],n;
  for(n=0;n<oldNode.childNodes.length;n++)oldKids.push(oldNode.childNodes[n]);
  for(n=0;n<newNode.childNodes.length;n++)newKids.push(newNode.childNodes[n]);
  var max=Math.max(oldKids.length,newKids.length);
  for(var i=0;i<max;i++)_patch(oldNode,oldKids[i],newKids[i]);
}

function patchInto(container,newChildren){
  var oldKids=[],i;
  for(i=0;i<container.childNodes.length;i++)oldKids.push(container.childNodes[i]);
  var max=Math.max(oldKids.length,newChildren.length);
  for(i=0;i<max;i++)_patch(container,oldKids[i],newChildren[i]);
}

function loadingView(full){return h('div',{className:'loading-box',style:full?{minHeight:'60vh'}:{}},h('div',{className:'spinner'+(full?' spinner-lg':'')}),t('loading'))}

function periodSelector(current,periods,onChange){
  var btns=[];for(var i=0;i<periods.length;i++){(function(p){btns.push(h('button',{className:'per'+(current===p.v?' on':''),onClick:function(){onChange(p.v)}},p.l))})(periods[i])}
  return h('div',{className:'periods'},btns)}

var _pageState={};
function paginationBar(key,total,pageSize){
  var page=_pageState[key]||0;var pages=Math.ceil(total/pageSize);
  if(pages<=1)return null;
  var start=page*pageSize;
  return h('div',{style:{display:'flex',justifyContent:'center',alignItems:'center',gap:'10px',padding:'10px 0',fontSize:'11px',color:'var(--tx2)'}},
    h('button',{className:'btn btn-xs',disabled:page===0,onClick:function(){_pageState[key]=page-1;R()}},'◀'),
    (start+1)+'–'+Math.min(start+pageSize,total)+' '+t('of_total')+' '+total,
    h('button',{className:'btn btn-xs',disabled:page>=pages-1,onClick:function(){_pageState[key]=page+1;R()}},'▶'))}
function pageSlice(key,items,pageSize){
  pageSize=pageSize||20;
  if(!items||!items.length)return [];
  if(!_pageState[key])_pageState[key]=0;
  var pages=Math.ceil(items.length/pageSize);
  var page=_pageState[key];
  if(page>=pages)page=pages-1;if(page<0)page=0;_pageState[key]=page;
  return items.slice(page*pageSize,page*pageSize+pageSize)}
function paginatedList(key,items,renderFn,pageSize){
  pageSize=pageSize||20;if(!items||!items.length)return null;
  var slice=pageSlice(key,items,pageSize);
  var bar=paginationBar(key,items.length,pageSize);
  return bar?h('div',null,slice.map(renderFn),bar):h('div',null,slice.map(renderFn))}

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

function isEditing(){
  var a=document.activeElement;
  if(!a)return false;
  var tag=(a.tagName||'').toLowerCase();
  return tag==='input'||tag==='textarea'||tag==='select'||a.isContentEditable===true}

// Since rendering now patches instead of rebuilding, a background refresh is
// safe even while a modal is open or a field has focus: it updates only the
// values that actually changed.
function Rbg(cb){R(cb)}

function _captureFocus(){
  var a=document.activeElement;
  if(!a||!a.id)return null;
  var f={id:a.id,st:null,en:null};
  try{f.st=a.selectionStart;f.en=a.selectionEnd}catch(e){}
  return f}
function _restoreFocus(f){
  if(!f)return;
  var el=document.getElementById(f.id);
  if(!el)return;
  try{el.focus();if(f.st!=null&&el.setSelectionRange)el.setSelectionRange(f.st,f.en)}catch(e){}}

var _rTimer=null;var _rCallbacks=[];
function R(cb){if(cb)_rCallbacks.push(cb);if(_rTimer)return;_rTimer=requestAnimationFrame(function(){_rTimer=null;_doRender();var cbs=_rCallbacks.slice();_rCallbacks=[];for(var i=0;i<cbs.length;i++){try{cbs[i]()}catch(e){console.error('render callback failed:',e)}}})}
function _slots(){
  var root=document.getElementById('root');
  var modal=document.getElementById('modal-slot');
  var app=document.getElementById('app-slot');
  if(!modal||!app){
    // Fixed slots keep positions stable, so a modal appearing never makes the
    // patcher mistake the app subtree for the modal subtree.
    root.replaceChildren();
    modal=document.createElement('div');modal.id='modal-slot';
    app=document.createElement('div');app.id='app-slot';
    root.appendChild(modal);root.appendChild(app);
  }
  return {modal:modal,app:app}}

function _doRender(){
  var s=_slots();
  // Safety net: patching preserves focus, but a node whose tag changed is
  // genuinely replaced, and then we put the caret back.
  var focus=_captureFocus();
  try{
    patchInto(s.modal, S.modal?[renderModal()]:[]);
    var body;
    if(S.loading)body=loadingView(true);
    else if(!S.auth)body=renderLogin();
    else body=renderApp();
    patchInto(s.app,[body]);
    if(document.activeElement!==(focus&&document.getElementById(focus.id)))_restoreFocus(focus);
    if(S.modal&&S.modal.t==='cfg')paintQr();
    if(S.tab==='monitor'&&window.Chart)drawMonitorCharts();
  }catch(err){
    console.error('R() error:',err);
    s.app.replaceChildren(h('div',{style:{color:'#ef4444',padding:'40px',fontFamily:'monospace',fontSize:'13px'}},
      h('b',null,t('render_error')),h('br'),h('pre',null,String(err&&err.message||err))));
  }
}

function _softUpdateLogin(){
  var el=document.querySelector('.ls');if(el)el.textContent=S.setup?t('create_admin_pw'):t('enter_admin_pw');
  var lt=document.querySelector('.lt');if(lt)lt.textContent=S.setup?t('initial_setup'):'';
  var btn=document.querySelector('.lc .btn-p');if(btn)btn.textContent=S.setup?t('create_password'):t('sign_in');
  var inp=document.querySelector('.lc input[type=password]');if(inp)inp.placeholder=t('password');
  document.querySelectorAll('.lg button').forEach(function(b,i){b.className=(i===0?S.lang==='en':S.lang==='ru')?'on':''});
  document.querySelectorAll('.tg button').forEach(function(b,i){b.className=([S.theme==='dark',S.theme==='light',S.theme==='system'][i])?'on':''});
}
function renderLogin(){
  var isS=S.setup;
  if(S.setupLocked){
    return h('div',{className:'lw'},h('div',{className:'lc'},
      h('div',{className:'lt'},t('setup_locked_title')),
      h('div',{className:'ls'},t('setup_locked_msg'))));
  }
  // Read from the DOM, never from a captured node: after a patch the element
  // created in this render may have been discarded in favour of the live one.
  var submit=function(){
    var el=document.getElementById('login-pw');
    if(!el)return;
    isS?doSetup(el.value):doLogin(el.value)};
  var card=h('div',{className:'lw'},h('div',{className:'lc'},
    h('div',{style:{textAlign:'center',marginBottom:'20px'}},h('img',{src:LOGO_FULL,alt:'TrustTunnel',className:'logo-img',style:{maxHeight:'56px',maxWidth:'260px',width:'auto',height:'auto',margin:'0 auto 12px'}})),
    h('div',{className:'lt'},isS?t('initial_setup'):''),
    h('div',{className:'ls'},isS?t('create_admin_pw'):t('enter_admin_pw')),
    h('div',{className:'fg'},h('input',{className:'input',type:'password',id:'login-pw',autocomplete:isS?'new-password':'current-password',placeholder:t('password'),style:{textAlign:'center'},onKeydown:function(e){if(e.key==='Enter'){e.preventDefault();submit()}}})),
    h('button',{className:'btn btn-p',style:{width:'100%',justifyContent:'center',padding:'12px',fontSize:'13px',borderRadius:'10px'},onClick:submit},isS?t('create_password'):t('sign_in')),
    h('div',{style:{display:'flex',justifyContent:'center',marginTop:'16px',gap:'8px'}},langThemeControls())));
  setTimeout(function(){var el=document.getElementById('login-pw');if(el&&!isEditing())el.focus()},FOCUS_DELAY_MS);
  return card;
}

function langThemeControls(){
  return [
    h('div',{className:'lg'},
      h('button',{className:S.lang==='en'?'on':'',onClick:function(){setLang('en')}},'EN'),
      h('button',{className:S.lang==='ru'?'on':'',onClick:function(){setLang('ru')}},'РУ')),
    h('div',{className:'tg'},
      h('button',{className:S.theme==='dark'?'on':'','aria-label':t('theme_dark'),onClick:function(){setTheme('dark')},title:t('theme_dark')},'☾'),
      h('button',{className:S.theme==='light'?'on':'','aria-label':t('theme_light'),onClick:function(){setTheme('light')},title:t('theme_light')},'☀'),
      h('button',{className:S.theme==='system'?'on':'','aria-label':t('theme_system'),onClick:function(){setTheme('system')},title:t('theme_system')},'⚙'))]}

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
        h('img',{src:LOGO_FULL,alt:'TrustTunnel',className:'logo-img',style:{height:'34px',width:'auto'}}),
        h('div',{className:'logo-s',style:{marginLeft:'8px'}},(S.status&&S.status.domain)||'')),
      h('div',{className:'bg'},
        langThemeControls(),
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

'''
