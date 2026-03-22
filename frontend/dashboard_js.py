DASHBOARD_JS = r'''
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
        h('button',{className:'btn btn-sm btn-p',onClick:function(){S.modal={t:'add'};R()}},t('quick_add_user')),
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
          h('thead',null,h('tr',null,h('th',null,t('restart_time')),h('th',null,t('restart_reason')),h('th',null,t('detail')))),
          h('tbody',null,S.restartHistory.slice(0,20).map(function(r){var reasonKey='reason_'+r.reason;var reasonText=t(reasonKey)!==reasonKey?t(reasonKey):r.reason;var det=r.detail||'';var detParts=det.split(':');var detReason=detParts[0]?'reason_'+detParts[0]:'';var detUser=detParts[1]||'';var detText=detReason&&t(detReason)!==detReason?t(detReason)+(detUser?' \u2014 '+detUser:''):det;return h('tr',null,
            h('td',null,r.ts||'\u2014'),
            h('td',null,reasonText),
            h('td',{style:{color:'var(--tx3)'}},detText))})))):
        h('div',{style:{color:'var(--tx3)',fontSize:'12px',textAlign:'center',padding:'12px 0'}},t('no_restart_history')))
  );
}

'''
