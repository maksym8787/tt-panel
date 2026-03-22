INIT_JS = r'''
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
