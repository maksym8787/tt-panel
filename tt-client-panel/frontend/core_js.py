CORE_JS = r'''var A='/api';
var POLL_MS=10000;
var TOAST_MS=3500;
var REQUEST_TIMEOUT_MS=20000;
var FOCUS_DELAY_MS=50;
var RELOAD_DELAY_MS=2000;

var S={auth:false,setup:false,setupLocked:false,minPwLen:12,loading:true,tab:'servers',
  servers:[],activeServerId:'',status:null,failoverLog:[],settings:{},
  toast:null,modal:null,netHistory:[],netPeriod:1,srvLatency:null,latPeriod:24,lang:localStorage.getItem('tt_lang')||'en',
  theme:localStorage.getItem('tt_theme')||'system',addMode:'deeplink',flPage:0,
  draft:{},staleTicks:0};

function t(k){return(T[S.lang]||T.en)[k]||T.en[k]||k}
function setLang(l){S.lang=l;localStorage.setItem('tt_lang',l);if(!S.auth){_patchLoginText()}else{R()}}
function setTheme(th){S.theme=th;localStorage.setItem('tt_theme',th);applyTheme();if(!S.auth){_patchLoginText()}else{R(function(){if(S.tab==='monitor')drawNetChart()})}}
function _patchLoginText(){
  var e=document.querySelector('.ls');if(e)e.textContent=S.setup?t('create_admin_pw'):t('enter_admin_pw');
  var lt=document.querySelector('.lt');if(lt)lt.textContent=S.setup?t('initial_setup'):'';
  var b=document.querySelector('.lc .btn-p');if(b)b.textContent=S.setup?t('create_password'):t('sign_in');
  var i=document.querySelector('.lc input[type=password]');if(i)i.placeholder=t('password');
  document.querySelectorAll('.lg button').forEach(function(b,i){b.className=(i===0?S.lang==='en':S.lang==='ru')?'on':''});
  document.querySelectorAll('.tg button').forEach(function(b,i){b.className=([S.theme==='dark',S.theme==='light',S.theme==='system'][i])?'on':''})}
function applyTheme(){document.documentElement.setAttribute('data-theme',S.theme)}

function _errMsg(d,r){
  var det=d&&d.detail;
  if(typeof det==='string')return det;
  if(Array.isArray(det)&&det.length){var f=det[0];return (f&&(f.msg||f.detail))||r.statusText||('HTTP '+r.status)}
  if(det&&typeof det==='object')return det.msg||det.detail||('HTTP '+r.status);
  return r.statusText||('HTTP '+r.status)}

function onUnauthorized(){
  if(!S.auth)return;
  S.auth=false;S.modal=null;S.status=null;S.servers=[];
  stopRefresh();
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
  var d={},txt='';
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

function fmtUptime(sec){if(!sec)return '—';var d=Math.floor(sec/86400),h=Math.floor((sec%86400)/3600),m=Math.floor((sec%3600)/60);if(d>0)return d+'d '+h+'h '+m+'m';if(h>0)return h+'h '+m+'m';return m+'m'}
function enc(s){return encodeURIComponent(s)}
function splitAddresses(v){return String(v||'').split(',').map(function(x){return x.trim()}).filter(Boolean)}

function withLoading(btn,fn){
  if(!btn)return Promise.resolve(fn());
  var orig=btn.textContent;btn.disabled=true;btn.textContent='…';
  return Promise.resolve(fn()).finally(function(){if(btn.isConnected){btn.disabled=false;btn.textContent=orig}})}

var _tipEl=null;
function _closeTip(){if(_tipEl&&_tipEl.parentNode)_tipEl.parentNode.removeChild(_tipEl);_tipEl=null}
function tip(key){
  var text=t('tip_'+key);
  if(!text||text===('tip_'+key))return null;
  return h('span',{style:{cursor:'pointer',fontSize:'11px',color:'var(--ac)',marginLeft:'4px',display:'inline-flex',alignItems:'center',justifyContent:'center',width:'16px',height:'16px',borderRadius:'50%',border:'1px solid var(--ac)',flexShrink:'0',position:'relative',userSelect:'none'},
    'aria-label':text,
    onClick:function(e){
      e.stopPropagation();
      var wasOpen=!!_tipEl;
      _closeTip();
      if(wasOpen)return;
      var pop=document.createElement('div');
      pop.style.cssText='position:fixed;z-index:9999;background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:10px 14px;font-size:12px;color:var(--tx);max-width:300px;box-shadow:0 4px 20px rgba(0,0,0,.3);line-height:1.5';
      pop.textContent=text;
      var rect=e.currentTarget.getBoundingClientRect();
      pop.style.top=(rect.bottom+6)+'px';
      pop.style.left=Math.max(8,Math.min(rect.left,window.innerWidth-310))+'px';
      document.body.appendChild(pop);
      _tipEl=pop;
      setTimeout(function(){document.addEventListener('click',function rm(){_closeTip();document.removeEventListener('click',rm)})},10)
    }},'ℹ')}
function fl(label,tipKey){return h('label',{className:'fl',style:{display:'flex',alignItems:'center'}},label,tipKey?tip(tipKey):null)}

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
    if(Array.isArray(x)){for(var j=0;j<x.length;j++)an(e,x[j])}
    else{an(e,x)}
  }
  if(deferValue!==null){e.value=deferValue;e.__val=deferValue}
  return e}

function an(e,x){if(x==null||x===false||x===undefined)return;if(typeof x==='number')x=String(x);if(typeof x==='string')e.appendChild(document.createTextNode(x));else if(x.nodeType)e.appendChild(x);else if(Array.isArray(x)){for(var i=0;i<x.length;i++)an(e,x[i])}}

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

// Draft-backed inputs: a background refresh must not wipe what the user typed.
function dinput(key,attrs){
  var a={};for(var k in attrs)a[k]=attrs[k];
  if(S.draft[key]===undefined)S.draft[key]=attrs.value||'';
  a.value=S.draft[key];
  a.onInput=function(e){S.draft[key]=e.target.value};
  return h('input',a)}
function dcheck(key,def){
  if(S.draft[key]===undefined)S.draft[key]=!!def;
  return h('input',{type:'checkbox',checked:S.draft[key],onChange:function(e){S.draft[key]=e.target.checked}})}
function dselect(key,def,options){
  if(S.draft[key]===undefined)S.draft[key]=def;
  return h('select',{className:'input',value:S.draft[key],onChange:function(e){S.draft[key]=e.target.value}},
    options.map(function(o){return h('option',{value:o.v,selected:o.v===S.draft[key]},o.l)}))}
function dval(key){return S.draft[key]===undefined?'':S.draft[key]}
function clearDraft(prefix){
  Object.keys(S.draft).forEach(function(k){if(k.indexOf(prefix)===0)delete S.draft[k]})}

async function checkAuth(){
  try{var r=await api('/auth-status');S.auth=r.authenticated;S.setup=r.setup_required;S.setupLocked=!!r.setup_locked;if(r.min_password_len)S.minPwLen=r.min_password_len}
  catch(e){S.auth=false}
  S.loading=false;R();
  if(S.auth){loadAll();startRefresh()}}
async function doLogin(pw){try{await api('/login',{method:'POST',body:JSON.stringify({password:pw})});S.auth=true;R();loadAll();startRefresh()}catch(e){toast(e.message,true)}}
async function doSetup(pw){
  if(!pw||pw.length<S.minPwLen){toast(t('pw_too_short').replace('{n}',S.minPwLen),true);return}
  try{await api('/setup',{method:'POST',body:JSON.stringify({password:pw})});S.setup=false;await doLogin(pw)}catch(e){toast(e.message,true)}}
async function doLogout(){
  try{await api('/logout',{method:'POST'})}
  catch(e){}
  finally{S.auth=false;S.modal=null;stopRefresh();R()}}
async function chgAdmin(cur,pw,btn){
  if(!cur){toast(t('current_password')+': '+t('required'),true);return}
  if(!pw||pw.length<S.minPwLen){toast(t('pw_too_short').replace('{n}',S.minPwLen),true);return}
  await withLoading(btn,async function(){
    try{
      await api('/change-password',{method:'POST',body:JSON.stringify({current_password:cur,password:pw})});
      S.modal=null;S.auth=false;stopRefresh();
      toast(t('changed_relogin'));R()}
    catch(e){toast(e.message,true)}})}

function isEditing(){
  var a=document.activeElement;
  if(!a)return false;
  var tag=(a.tagName||'').toLowerCase();
  return tag==='input'||tag==='textarea'||tag==='select'||a.isContentEditable===true}

// Rendering patches instead of rebuilding, so a background refresh is safe
// even while a modal is open or a field has focus.
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
    root.replaceChildren();
    modal=document.createElement('div');modal.id='modal-slot';
    app=document.createElement('div');app.id='app-slot';
    root.appendChild(modal);root.appendChild(app);
  }
  return {modal:modal,app:app}}

function _doRender(){
  var s=_slots();
  var focus=_captureFocus();
  try{
    patchInto(s.modal, S.modal?[renderModal()]:[]);
    var body;
    if(S.loading)body=h('div',{className:'loading-box',style:{minHeight:'60vh'}},h('div',{className:'spinner spinner-lg'}),t('loading'));
    else if(!S.auth)body=renderLogin();
    else body=renderApp();
    patchInto(s.app,[body]);
    if(document.activeElement!==(focus&&document.getElementById(focus.id)))_restoreFocus(focus);
    if(S.tab==='monitor'){drawNetChart();drawLatencyChart()}
  }catch(err){
    console.error('R() error:',err);
    s.app.replaceChildren(h('div',{style:{color:'#ef4444',padding:'40px',fontFamily:'monospace',fontSize:'13px'}},
      h('b',null,t('render_error')),h('br'),h('pre',null,String(err&&err.message||err))));
  }
}

function langThemeBar(wrap){
  var controls=[
    h('div',{className:'lg'},
      h('button',{className:S.lang==='en'?'on':'',onClick:function(){setLang('en')}},'EN'),
      h('button',{className:S.lang==='ru'?'on':'',onClick:function(){setLang('ru')}},'РУ')),
    h('div',{className:'tg'},
      h('button',{className:S.theme==='dark'?'on':'','aria-label':t('theme_dark'),onClick:function(){setTheme('dark')}},'☾'),
      h('button',{className:S.theme==='light'?'on':'','aria-label':t('theme_light'),onClick:function(){setTheme('light')}},'☀'),
      h('button',{className:S.theme==='system'?'on':'','aria-label':t('theme_system'),onClick:function(){setTheme('system')}},'⚙'))];
  return wrap===false?controls
    :h('div',{style:{display:'flex',justifyContent:'center',marginTop:'16px',gap:'8px'}},controls)}

function renderLogin(){
  var isS=S.setup;
  if(S.setupLocked){
    return h('div',{className:'lw'},h('div',{className:'lc'},
      h('div',{className:'lt'},t('setup_locked_title')),
      h('div',{className:'ls'},t('setup_locked_msg'))));
  }
  var submit=function(){var el=document.getElementById('login-pw');if(el)isS?doSetup(el.value):doLogin(el.value)};
  var card=h('div',{className:'lw'},h('div',{className:'lc'},
    h('div',{style:{textAlign:'center',marginBottom:'20px'}},h('img',{src:'/static/logo-full.png',alt:'TrustTunnel',className:'logo-img',style:{maxHeight:'56px',maxWidth:'260px',width:'auto',height:'auto',margin:'0 auto 12px'}})),
    h('div',{className:'lt'},isS?t('initial_setup'):''),
    h('div',{className:'ls'},isS?t('create_admin_pw'):t('enter_admin_pw')),
    h('div',{className:'fg'},h('input',{className:'input',type:'password',id:'login-pw',autocomplete:isS?'new-password':'current-password',placeholder:t('password'),style:{textAlign:'center'},
      onKeydown:function(e){if(e.key==='Enter'){e.preventDefault();submit()}}})),
    h('button',{className:'btn btn-p',style:{width:'100%',justifyContent:'center',padding:'12px',fontSize:'13px',borderRadius:'10px'},onClick:submit},isS?t('create_password'):t('sign_in')),
    langThemeBar()));
  setTimeout(function(){var el=document.getElementById('login-pw');if(el&&!isEditing())el.focus()},FOCUS_DELAY_MS);
  return card;
}

function renderApp(){
  var tabs=[{id:'servers',label:t('servers')},{id:'monitor',label:t('monitor')},{id:'settings',label:t('settings')}];
  return h('div',{className:'app fade-in'},
    h('div',{className:'hdr'},
      h('div',{className:'logo'},
        h('img',{src:'/static/logo-full.png',alt:'TrustTunnel',className:'logo-img',style:{height:'34px',width:'auto'}}),
        h('div',{className:'logo-s',style:{marginLeft:'8px'}},'Client')),
      h('div',{className:'bg'},
        langThemeBar(false),
        h('button',{className:'btn btn-xs btn-ghost',onClick:function(){S.modal={t:'chgadmin'};R()}},t('password_btn')),
        h('button',{className:'btn btn-xs btn-ghost',onClick:doLogout},t('logout')))),
    h('div',{className:'tabs'},tabs.map(function(tb){return h('button',{className:'tab'+(S.tab===tb.id?' on':''),
      onClick:function(){S.tab=tb.id;if(tb.id==='servers')loadAll();if(tb.id==='monitor'){loadStatus();loadFailoverLog();loadServerLatency();loadNetHistory().then(function(){R(function(){drawNetChart();drawLatencyChart()})})}if(tb.id==='settings')loadSettings();R()}},tb.label)})),
    h('div',{className:'tab-content'},S.tab==='servers'?renderServers():S.tab==='monitor'?renderMonitor():renderSettings()));
}

function renderModal(){
  var m=S.modal;if(!m)return h('div');
  var close=function(){clearDraft('m_');S.modal=null;R()};
  var content;
  if(m.t==='confirm'){
    content=h('div',{className:'md',role:'alertdialog','aria-modal':'true'},
      h('div',{className:'md-t'},m.title||t('confirm')),
      h('div',{style:{fontSize:'13px',color:'var(--tx2)',marginBottom:'16px'}},m.msg||''),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-d',onClick:function(e){if(m.onOk)m.onOk(e.currentTarget)}},t('confirm')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
  }else if(m.t==='edit'){
    var s=m.s;
    content=h('div',{className:'md',style:{maxWidth:'540px'},role:'dialog','aria-modal':'true'},
      h('div',{className:'md-t'},t('edit')+': '+s.name),
      h('div',{className:'grid grid2',style:{gap:'10px'}},
        h('div',{className:'fg'},fl(t('name'),'srv_name'),dinput('m_name',{className:'input',id:'m-name',value:s.name||''})),
        h('div',{className:'fg'},fl(t('hostname'),'srv_hostname'),dinput('m_host',{className:'input input-m',id:'m-host',value:s.hostname||''}))),
      h('div',{className:'fg'},fl(t('address'),'srv_address'),dinput('m_addr',{className:'input input-m',id:'m-addr',value:(s.addresses||[]).join(', '),placeholder:'host:443, host2:443'})),
      h('div',{className:'grid grid2',style:{gap:'10px'}},
        h('div',{className:'fg'},fl(t('username'),'srv_username'),dinput('m_user',{className:'input',id:'m-user',autocomplete:'off',value:s.username||''})),
        h('div',{className:'fg'},fl(t('password'),'srv_password'),dinput('m_pass',{className:'input',id:'m-pass',type:'password',autocomplete:'new-password',value:s.password||''}))),
      h('div',{className:'grid grid2',style:{gap:'10px'}},
        h('div',{className:'fg'},fl(t('protocol'),'srv_protocol'),dselect('m_proto',s.upstream_protocol||'http2',[{v:'http2',l:'HTTP/2'},{v:'http3',l:'HTTP/3'}])),
        h('div',{className:'fg'},fl('SNI','srv_sni'),dinput('m_sni',{className:'input input-m',id:'m-sni',value:s.custom_sni||'',placeholder:t('hostname')}))),
      h('div',{style:{display:'flex',gap:'16px',marginBottom:'14px'}},
        h('label',{style:{display:'flex',alignItems:'center',gap:'6px',fontSize:'12px',cursor:'pointer'}},dcheck('m_ipv6',s.has_ipv6!==false),'IPv6'),
        h('label',{style:{display:'flex',alignItems:'center',gap:'6px',fontSize:'12px',cursor:'pointer'}},dcheck('m_dpi',!!s.anti_dpi),'Anti-DPI'),
        h('label',{style:{display:'flex',alignItems:'center',gap:'6px',fontSize:'12px',cursor:'pointer'}},dcheck('m_enabled',s.enabled!==false),t('enabled'))),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(e){
          var addrs=splitAddresses(dval('m_addr'));
          if(!addrs.length)addrs=[dval('m_host')+':443'];
          editServer(s.id,{name:dval('m_name'),hostname:dval('m_host'),addresses:addrs,
            username:dval('m_user'),password:dval('m_pass'),upstream_protocol:dval('m_proto'),
            custom_sni:dval('m_sni'),has_ipv6:!!S.draft.m_ipv6,anti_dpi:!!S.draft.m_dpi,
            enabled:!!S.draft.m_enabled},e.currentTarget)}},t('save')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
  }else if(m.t==='chgadmin'){
    content=h('div',{className:'md',role:'dialog','aria-modal':'true'},
      h('div',{className:'md-t'},t('change_password')),
      h('div',{className:'fg'},h('label',{className:'fl',for:'m-cur'},t('current_password')),
        dinput('m_cur',{className:'input',id:'m-cur',type:'password',autocomplete:'current-password',placeholder:t('current_password')})),
      h('div',{className:'fg'},h('label',{className:'fl',for:'m-new'},t('new_password')),
        dinput('m_new',{className:'input',id:'m-new',type:'password',autocomplete:'new-password',placeholder:t('new_password')})),
      h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'10px'}},t('pw_too_short').replace('{n}',S.minPwLen)),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(e){chgAdmin(dval('m_cur'),dval('m_new'),e.currentTarget)}},t('save')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
    _focusOnce('m-cur');
  }
  return h('div',{className:'mo',onClick:function(e){if(e.target.className&&e.target.className.indexOf('mo')!==-1)close()}},content||h('div'));
}

function _focusOnce(id){
  if(!S.modal||S.modal._focused)return;
  S.modal._focused=true;
  setTimeout(function(){var el=document.getElementById(id);if(el)el.focus()},FOCUS_DELAY_MS)}
'''
