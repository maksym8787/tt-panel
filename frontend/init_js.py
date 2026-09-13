INIT_JS = r'''
function renderLogs(){
  return h('div',{className:'tab-content'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'12px'}},
      h('div',{style:{fontSize:'13px',fontWeight:'600'}},t('service_logs')),
      h('button',{className:'btn btn-sm',onClick:loadLogs},t('refresh'))),
    S.logsLoading?h('div',null,h('div',{className:'skeleton skel-row'}),h('div',{className:'skeleton skel-row'}),h('div',{className:'skeleton skel-row'}),h('div',{className:'skeleton skel-row'}),h('div',{className:'skeleton skel-row'})):h('div',{className:'lb'},S.logs===null?t('click_refresh'):S.logs===''?t('empty_log'):S.logs));
}

// Modal field values live in S.modal.d so a background re-render cannot wipe them.
function mdraft(key,attrs){
  var m=S.modal;m.d=m.d||{};
  var a={};for(var k in attrs)a[k]=attrs[k];
  a.value=m.d[key]||'';
  a.onInput=function(e){m.d[key]=e.target.value};
  return h('input',a)}
function dval(key){return (S.modal&&S.modal.d&&S.modal.d[key])||''}

function renderModal(){
  var m=S.modal;if(!m)return h('div');
  var close=function(){S.modal=null;R()};
  var content;
  if(m.t==='add'){
    content=h('div',{className:'md',role:'dialog','aria-modal':'true','aria-label':t('add_vpn_user')},
      h('div',{className:'md-t'},t('add_vpn_user')),
      h('div',{className:'fg'},h('label',{className:'fl',for:'md-user'},t('username')),
        mdraft('username',{className:'input',id:'md-user',autocomplete:'off',placeholder:t('username_placeholder')})),
      h('div',{className:'fg'},h('label',{className:'fl',for:'md-pass'},t('password_empty_auto')),
        mdraft('password',{className:'input input-m',id:'md-pass',autocomplete:'new-password',placeholder:'auto'})),
      h('div',{className:'fg'},h('label',{className:'fl',for:'md-note'},t('note')),
        mdraft('note',{className:'input',id:'md-note',placeholder:t('note_placeholder'),maxLength:200})),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(e){addUser(dval('username'),dval('password'),dval('note').trim(),e.currentTarget)}},t('create')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
    _focusOnce('md-user');
  } else if(m.t==='cfg'){
    content=h('div',{className:'md',role:'dialog','aria-modal':'true','aria-label':t('config')},
      h('div',{className:'md-t'},t('config_for')+': '+m.u+' ('+m.f+')'),
      m.f==='deeplink'?h('div',{className:'qc'},h('div',{className:'qr',id:'qr-t'}),
        h('div',{style:{fontSize:'11px',color:'var(--tx3)',textAlign:'center',wordBreak:'break-all',maxWidth:'300px',marginTop:'4px'}},m.c)):
        h('div',{className:'cb'},m.c),
      h('div',{className:'bg',style:{marginTop:'14px'}},
        h('button',{className:'btn btn-p btn-sm',onClick:function(){copyText(m.c)}},t('copy')),
        h('button',{className:'btn btn-sm',onClick:close},t('close'))));
  } else if(m.t==='confirm'){
    content=h('div',{className:'md',role:'alertdialog','aria-modal':'true','aria-label':m.title||t('confirm')},
      h('div',{className:'md-t'},m.title||t('confirm')),
      h('div',{style:{fontSize:'13px',color:'var(--tx2)',marginBottom:'16px'}},m.msg||''),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-d',onClick:function(e){if(m.onConfirm)m.onConfirm(e.currentTarget)}},t('confirm')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
  } else if(m.t==='chgpass'){
    content=h('div',{className:'md',role:'dialog','aria-modal':'true','aria-label':t('change_password')},
      h('div',{className:'md-t'},t('change_password')+': "'+m.u+'"'),
      h('div',{className:'fg'},h('label',{className:'fl',for:'md-np'},t('new_password')),
        mdraft('np',{className:'input input-m',id:'md-np',type:'password',autocomplete:'new-password',placeholder:t('new_password')})),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(e){doChgPass(m.u,dval('np'),e.currentTarget)}},t('change')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
    _focusOnce('md-np');
  } else if(m.t==='chgadmin'){
    content=h('div',{className:'md',role:'dialog','aria-modal':'true','aria-label':t('change_password')},
      h('div',{className:'md-t'},t('change_password')),
      h('div',{className:'fg'},h('label',{className:'fl',for:'md-cur'},t('current_password')),
        mdraft('cur',{className:'input',id:'md-cur',type:'password',autocomplete:'current-password',placeholder:t('current_password')})),
      h('div',{className:'fg'},h('label',{className:'fl',for:'md-new'},t('new_admin_password')),
        mdraft('np',{className:'input',id:'md-new',type:'password',autocomplete:'new-password',placeholder:t('new_admin_password')})),
      h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'10px'}},t('pw_too_short').replace('{n}',S.minPwLen)),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-p',onClick:function(e){doChgAdmin(dval('cur'),dval('np'),e.currentTarget)}},t('change')),
        h('button',{className:'btn',onClick:close},t('cancel'))));
    _focusOnce('md-cur');
  }
  return h('div',{className:'mo',onClick:function(e){if(e.target.className&&e.target.className.indexOf&&e.target.className.indexOf('mo')!==-1)close()}},content||h('div'));
}

// Focus a modal field on first paint only, so later re-renders don't steal the caret.
function _focusOnce(id){
  if(!S.modal||S.modal._focused)return;
  S.modal._focused=true;
  setTimeout(function(){var el=document.getElementById(id);if(el)el.focus()},FOCUS_DELAY_MS)}

document.addEventListener('keydown',function(e){if(e.key==='Escape'&&S.modal){S.modal=null;R()}});

// ─── Init ───────────────────────────────────────────────
function _markActivity(){S.lastActivity=Date.now()}
document.addEventListener('pointerdown',_markActivity,{passive:true});
document.addEventListener('keydown',_markActivity);
document.addEventListener('scroll',_markActivity,{passive:true});
setInterval(function(){if(S.auth&&S.panelSettings&&S.panelSettings.session_ttl){if((Date.now()-S.lastActivity)>S.panelSettings.session_ttl*1000){doLogout()}}},60000);
applyTheme();
checkAuth();

var _refreshDash=null,_refreshMon=null,_refreshingDash=false,_refreshingMon=false;
function startRefreshTimers(){
  stopRefreshTimers();
  _refreshDash=setInterval(async function(){
    if(_refreshingDash||!S.auth||S.tab!=='dashboard')return;
    _refreshingDash=true;
    try{await Promise.all([_loadDash(),_loadSummary(),_checkPendingReload()]);Rbg()}
    finally{_refreshingDash=false}
  },POLL_DASH_MS);
  _refreshMon=setInterval(async function(){
    if(_refreshingMon||!S.auth||S.tab!=='monitor')return;
    _refreshingMon=true;
    try{await Promise.all([_loadHistory(),_loadTraffic(),_loadConnTimeline(),_loadOnline(),_loadConns(),_loadPerUser()]);Rbg(drawMonitorCharts)}
    finally{_refreshingMon=false}
  },POLL_MON_MS);
}
function stopRefreshTimers(){if(_refreshDash){clearInterval(_refreshDash);_refreshDash=null}if(_refreshMon){clearInterval(_refreshMon);_refreshMon=null}}
startRefreshTimers();
document.addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden'){stopRefreshTimers()}else if(S.auth){startRefreshTimers()}});
'''
