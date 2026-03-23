PREAMBLE_JS = r'''
var LOGO_ICON='/static/favicon.png';
var LOGO_FULL='/static/logo-full.png';
var A='/api';
'''

CORE_JS = r'''
function t(k){return (T[S.lang]||T.en)[k]||T.en[k]||k}
function setLang(l){S.lang=l;localStorage.setItem('tt_lang',l);if(!S.auth){_softUpdateLogin()}else{R()}}
function setTheme(th){S.theme=th;localStorage.setItem('tt_theme',th);applyTheme();if(!S.auth){_softUpdateLogin()}}
function applyTheme(){document.documentElement.setAttribute('data-theme',S.theme)}
var S={auth:false,setup:false,loading:true,tab:'dashboard',status:null,users:[],logs:null,settings:{},
  history:null,traffic:null,conns:null,online:null,summary:null,toast:null,modal:null,dbSize:null,
  connTimeline:null,activeIps:{},monPeriod:24,connPeriod:24,pendingReload:false,userFilter:'',userSort:'name_asc',monLoading:false,logsLoading:false,structuredSettings:null,
  lang:localStorage.getItem('tt_lang')||'en',theme:localStorage.getItem('tt_theme')||'system',
  restartHistory:null,userNotes:{},panelSettings:null,lastActivity:Date.now()};

async function api(p,o){o=o||{};var r=await fetch(A+p,{headers:{'Content-Type':'application/json'},credentials:'same-origin',...o});var d=await r.json();if(!r.ok)throw new Error(d.detail||r.statusText);return d}
function toast(m,e){S.toast={m:m,e:!!e};R();setTimeout(function(){S.toast=null;R()},3500)}
function fmt(b){if(b==null)return '0 B';if(b>=1099511627776)return(b/1099511627776).toFixed(2)+' TB';if(b>=1073741824)return(b/1073741824).toFixed(2)+' GB';if(b>=1048576)return(b/1048576).toFixed(1)+' MB';if(b>=1024)return(b/1024).toFixed(0)+' KB';return b+' B'}
function fmtShort(b){if(b==null)return '0';if(b>=1099511627776)return(b/1099511627776).toFixed(1)+' TB';if(b>=1073741824)return(b/1073741824).toFixed(1)+' GB';if(b>=1048576)return(b/1048576).toFixed(0)+' MB';if(b>=1024)return(b/1024).toFixed(0)+' KB';return b+' B'}
function ts2t(ts){var d=new Date(ts*1000);var hh=String(d.getHours()).padStart(2,'0')+':00';if(d.getHours()===0)return d.getDate()+'.'+(d.getMonth()+1)+' '+hh;return hh}
function ts2h(ts){return ts2t(ts)}
function ts2dt(ts){return new Date(ts*1000).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
function ago(ts){var d=Math.floor(Date.now()/1000-ts);if(d<60)return d+' '+t('s_ago');if(d<3600)return Math.floor(d/60)+' '+t('m_ago');if(d<86400)return Math.floor(d/3600)+' '+t('h_ago');return Math.floor(d/86400)+' '+t('d_ago')}
function fmtUptime(sec){if(!sec)return '\u2014';var d=Math.floor(sec/86400),h=Math.floor((sec%86400)/3600),m=Math.floor((sec%3600)/60);if(d>0)return d+'d '+h+'h '+m+'m';if(h>0)return h+'h '+m+'m';return m+'m'}

function withLoading(btn,fn){
  if(!btn)return fn();
  var orig=btn.textContent;btn.disabled=true;btn.textContent='...';
  return Promise.resolve(fn()).finally(function(){if(btn.parentNode){btn.disabled=false;btn.textContent=orig}})}

async function checkAuth(){try{var r=await api('/auth-status');S.auth=r.authenticated;S.setup=r.setup_required}catch(e){S.auth=false}S.loading=false;R()}
async function doLogin(pw){try{await api('/login',{method:'POST',body:JSON.stringify({password:pw})});S.auth=true;loadAll()}catch(e){toast(e.message,true)}R()}
async function doSetup(pw){try{await api('/setup',{method:'POST',body:JSON.stringify({password:pw})});S.setup=false;await doLogin(pw)}catch(e){toast(e.message,true)}}
async function doLogout(){await api('/logout',{method:'POST'});S.auth=false;R()}

async function loadAll(){
  await Promise.all([_loadDash(),_loadSummary(),_checkPendingReload()]);
  R()
}
async function loadDash(){await _loadDash();R()}
async function _loadDash(){try{var p=await Promise.all([api('/status'),api('/users')]);S.status=p[0];S.users=p[1].users;if(S.status&&S.status.domain)document.title='TTAdmin - '+S.status.domain}catch(e){toast(e.message,true)}await _loadActiveIps();api('/restart-history').then(function(d){S.restartHistory=d.history}).catch(function(){});api('/user-notes').then(function(d){S.userNotes=d.notes;R()}).catch(function(){});api('/panel-settings').then(function(d){S.panelSettings=d.settings}).catch(function(){})}
async function _loadSummary(){try{S.summary=await api('/monitoring/summary')}catch(e){}}
async function _loadHistory(h){if(h!=null)S.monPeriod=h;try{S.history=await api('/monitoring/history?hours='+S.monPeriod)}catch(e){toast(e.message,true)}}
async function _loadConns(h){if(h!=null)S.connPeriod=h;try{S.conns=await api('/monitoring/connections?hours='+S.connPeriod)}catch(e){toast(e.message,true)}}
async function _loadConnTimeline(){try{S.connTimeline=await api('/monitoring/conn-timeline?hours='+S.monPeriod)}catch(e){}}
async function _loadOnline(){try{S.online=await api('/monitoring/online')}catch(e){}}
async function _loadDbSize(){try{S.dbSize=await api('/monitoring/db-size')}catch(e){}}
async function _loadActiveIps(){try{var r=await api('/active-ips');S.activeIps=r.active_ips||{}}catch(e){}}
async function _checkPendingReload(){try{var r=await api('/pending-reload');S.pendingReload=r.pending}catch(e){}}
async function loadHistory(h){await Promise.all([_loadHistory(h),_loadTraffic(),_loadConnTimeline()]);R(drawMonitorCharts)}
async function _loadTraffic(h){try{var hours=h||S.monPeriod||24;S.traffic=await api('/monitoring/traffic?hours='+hours)}catch(e){}}
async function loadTraffic(d){await _loadTraffic(d);R(drawTrafficChart)}
async function loadConns(h){await _loadConns(h);R()}
async function loadOnline(){await _loadOnline();R()}
async function loadLogs(){S.logsLoading=true;R();try{var r=await api('/logs?lines=200');S.logs=r.logs||'(empty log file)'}catch(e){S.logs='Error: '+e.message;toast(e.message,true)}S.logsLoading=false;R()}
async function loadSettings(){try{S.settings=await api('/settings')}catch(e){toast(e.message,true)}api('/settings/structured').then(function(d){S.structuredSettings=d;R()}).catch(function(){});R()}
async function loadMonitorAll(){
  S.monLoading=true;R();
  await Promise.all([_loadHistory(),_loadTraffic(),_loadConnTimeline(),_loadOnline(),_loadConns(),_loadDbSize()]);
  S.monLoading=false;R(drawMonitorCharts)
}
function drawMonitorCharts(){if(!window.Chart){setTimeout(drawMonitorCharts,200);return}drawAllCharts();drawTrafficChart();drawConnChart()}

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
async function applyReload(btn){await withLoading(btn,async function(){try{await api('/apply-reload',{method:'POST'});toast(t('service')+' '+t('restart').toLowerCase());S.pendingReload=false;R();setTimeout(loadDash,2000)}catch(e){toast(e.message,true)}})}

function h(t,a){var e=document.createElement(t);var deferValue=null;if(a){var keys=Object.keys(a);for(var ki=0;ki<keys.length;ki++){var k=keys[ki],v=a[k];if(k==='style'&&typeof v==='object')Object.assign(e.style,v);else if(k.substr(0,2)==='on')e.addEventListener(k.slice(2).toLowerCase(),v);else if(k==='className')e.className=v;else if(k==='innerHTML')e.innerHTML=v;else if(k==='value'){deferValue=v}else if(k==='checked'||k==='selected'||k==='disabled'){if(v!==false&&v!=null)e[k]=v}else e.setAttribute(k,v)}}for(var i=2;i<arguments.length;i++){var x=arguments[i];if(Array.isArray(x)){for(var j=0;j<x.length;j++)appendNode(e,x[j])}else{appendNode(e,x)}}if(deferValue!==null)e.value=deferValue;return e}
function appendNode(e,x){if(x==null||x===false||x===undefined)return;if(typeof x==='number')x=String(x);if(typeof x==='string')e.appendChild(document.createTextNode(x));else if(x.nodeType)e.appendChild(x);else if(Array.isArray(x)){for(var i=0;i<x.length;i++)appendNode(e,x[i])}}

function loadingView(full){return h('div',{className:'loading-box',style:full?{minHeight:'60vh'}:{}},h('div',{className:'spinner'+(full?' spinner-lg':'')}),t('loading'))}

function periodSelector(current,periods,onChange){
  var btns=[];for(var i=0;i<periods.length;i++){(function(p){btns.push(h('button',{className:'per'+(current===p.v?' on':''),onClick:function(){onChange(p.v)}},p.l))})(periods[i])}
  return h('div',{className:'periods'},btns)}

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

var _rTimer=null;var _rCallbacks=[];
function R(cb){if(cb)_rCallbacks.push(cb);if(_rTimer)return;_rTimer=requestAnimationFrame(function(){_rTimer=null;_doRender();var cbs=_rCallbacks.slice();_rCallbacks=[];for(var i=0;i<cbs.length;i++)cbs[i]()})}
function _doRender(){
  var root=document.getElementById('root');
  var scrollY=window.scrollY;
  try{
  var frag=document.createDocumentFragment();
  if(S.toast)frag.appendChild(h('div',{className:'toast '+(S.toast.e?'toast-err':'toast-ok')},S.toast.m));
  if(S.modal)frag.appendChild(renderModal());
  if(S.loading){frag.appendChild(loadingView(true));root.replaceChildren(frag);return}
  if(!S.auth){frag.appendChild(renderLogin());root.replaceChildren(frag);return}
  frag.appendChild(renderApp());
  root.replaceChildren(frag);
  window.scrollTo(0,scrollY);
  }catch(err){var msg=String(err.message||err).replace(/\x3c/g,'&lt;');root.innerHTML='\x3cdiv style="color:#ef4444;padding:40px;font-family:monospace;font-size:13px"\x3e\x3cb\x3eRender error:\x3c/b\x3e\x3cbr\x3e\x3cpre\x3e'+msg+'\x3c/pre\x3e\x3c/div\x3e';console.error('R() error:',err)}
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
  setTimeout(function(){if(pw){pw.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();(isS?doSetup:doLogin)(pw.value)}});pw.focus()}},50);
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

'''
