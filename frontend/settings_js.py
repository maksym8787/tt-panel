SETTINGS_JS = r'''
var _vpnEdits={};
var _rulesEdits=null;
var _settingsExpand={protocol:false,rawToml:false};
function settingToggle(obj,key,label){
  return h('div',{style:{display:'flex',alignItems:'center',gap:'6px'}},
    h('button',{className:'btn btn-xs'+(obj[key]?' btn-p':''),style:{minWidth:'40px'},onClick:function(){obj[key]=!obj[key];R()}},obj[key]?'ON':'OFF'),
    h('span',{style:{fontSize:'11px',color:'var(--tx2)'}},label))
}
function settingNumber(obj,key,label,suffix,min,max){
  return h('div',{style:{marginBottom:'8px'}},
    h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'3px'}},label),
    h('div',{style:{display:'flex',alignItems:'center',gap:'4px'}},
      h('input',{className:'input',type:'number',min:String(min||0),max:String(max||999999999),style:{width:'100px',padding:'4px 8px',fontSize:'12px'},value:String(obj[key]||0),onChange:function(e){obj[key]=parseInt(e.target.value)||0}}),
      suffix?h('span',{style:{fontSize:'10px',color:'var(--tx3)'}},suffix):null))
}
function settingText(obj,key,label,wide){
  return h('div',{style:{marginBottom:'8px',flex:wide?'1':'none'}},
    h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'3px'}},label),
    h('input',{className:'input',type:'text',style:{width:wide?'100%':'200px',padding:'4px 8px',fontSize:'12px'},value:String(obj[key]||''),onChange:function(e){obj[key]=e.target.value}}))
}
function renderSettings(){
  var s=S.settings;if(!s.vpn_toml&&s.vpn_toml!==''){loadSettings();return h('div',{className:'tab-content'},h('div',{className:'skeleton skel-card'}),h('div',{className:'skeleton skel-card'}))}
  var va,ra;var ps=S.panelSettings||{};
  var ttlOpts=[{v:300,l:'5 '+t('minutes')},{v:900,l:'15 '+t('minutes')},{v:1800,l:'30 '+t('minutes')},{v:3600,l:'1h'},{v:14400,l:'4h'},{v:43200,l:'12h'},{v:86400,l:'24h'}];
  var renewOn=ps.auto_renew_enabled!==false;
  var ss=S.structuredSettings;
  var vpn=(ss&&ss.vpn)?Object.assign({},ss.vpn,_vpnEdits):{};
  var timeouts=(ss&&ss.timeouts)?Object.assign({},ss.timeouts,_vpnEdits._timeouts||{}):{};
  var http2=(ss&&ss.http2)?Object.assign({},ss.http2,_vpnEdits._http2||{}):{};
  var quic=(ss&&ss.quic)?Object.assign({},ss.quic,_vpnEdits._quic||{}):{};
  var metrics=(ss&&ss.metrics)?Object.assign({},ss.metrics,_vpnEdits._metrics||{}):{};
  var routing=(ss&&ss.routing)?Object.assign({},ss.routing,_vpnEdits._routing||{}):{};
  var rules=(ss&&ss.rules)?ss.rules.slice():[];
  if(_rulesEdits)rules=_rulesEdits;
  var hosts=(ss&&ss.hosts)?ss.hosts:[];
  var sections=[
    h('div',{className:'grid grid2 section-gap'},
      h('div',{className:'stat'},
        h('div',{className:'stat-l'},t('session_timeout')),
        h('select',{className:'input',style:{marginTop:'8px'},value:String(ps.session_ttl||86400),onChange:function(e){var val=parseInt(e.target.value);api('/panel-settings',{method:'PUT',body:JSON.stringify({session_ttl:val})}).then(function(){if(!S.panelSettings)S.panelSettings={};S.panelSettings.session_ttl=val;toast(t('saved'))}).catch(function(er){toast(er.message,true)})}},ttlOpts.map(function(o){return h('option',{value:String(o.v),selected:o.v===(ps.session_ttl||86400)},o.l)}))),
      h('div',{className:'stat'},
        h('div',{className:'stat-l'},t('cert_auto_renew')),
        h('div',{style:{display:'flex',alignItems:'center',gap:'10px',marginTop:'8px'}},
          h('button',{className:'btn btn-sm'+(renewOn?' btn-d':' btn-p'),onClick:function(){var nv=!renewOn;api('/panel-settings',{method:'PUT',body:JSON.stringify({auto_renew_enabled:nv})}).then(function(){if(!S.panelSettings)S.panelSettings={};S.panelSettings.auto_renew_enabled=nv;toast(t('saved'));R()}).catch(function(er){toast(er.message,true)})}},renewOn?t('btn_disable'):t('btn_enable')),
          h('div',{style:{fontSize:'10px',color:'var(--tx3)'}},t('cert_renew_days')+':'),
          h('input',{className:'input',type:'number',min:'1',max:'60',style:{width:'60px',padding:'4px 8px',fontSize:'12px'},value:String(ps.auto_renew_days||10),onChange:function(e){var val=parseInt(e.target.value);if(val<1||val>60)return;api('/panel-settings',{method:'PUT',body:JSON.stringify({auto_renew_days:val})}).then(function(){if(!S.panelSettings)S.panelSettings={};S.panelSettings.auto_renew_days=val;toast(t('saved'))}).catch(function(er){toast(er.message,true)})}})))),
    h('div',{className:'grid grid2 section-gap'},
      h('div',{className:'stat'},
        h('div',{className:'stat-l'},t('max_history_days')),
        h('div',{style:{display:'flex',alignItems:'center',gap:'8px',marginTop:'8px'}},
          h('input',{className:'input',type:'number',min:'1',max:'365',style:{width:'80px',padding:'4px 8px',fontSize:'12px'},value:String(ps.max_history_days||30),onChange:function(e){var val=parseInt(e.target.value);if(val<1||val>365)return;api('/panel-settings',{method:'PUT',body:JSON.stringify({max_history_days:val})}).then(function(){if(!S.panelSettings)S.panelSettings={};S.panelSettings.max_history_days=val;toast(t('saved'))}).catch(function(er){toast(er.message,true)})}}),
          h('span',{style:{fontSize:'11px',color:'var(--tx3)'}},t('days')))),
      h('div',{className:'stat'},
        h('div',{className:'stat-l'},t('max_log_size')),
        h('div',{style:{display:'flex',alignItems:'center',gap:'8px',marginTop:'8px'}},
          h('input',{className:'input',type:'number',min:'5',max:'500',style:{width:'80px',padding:'4px 8px',fontSize:'12px'},value:String(ps.max_log_mb||50),onChange:function(e){var val=parseInt(e.target.value);if(val<5||val>500)return;api('/panel-settings',{method:'PUT',body:JSON.stringify({max_log_mb:val})}).then(function(){if(!S.panelSettings)S.panelSettings={};S.panelSettings.max_log_mb=val;toast(t('saved'))}).catch(function(er){toast(er.message,true)})}}),
          h('span',{style:{fontSize:'11px',color:'var(--tx3)'}},'MB'),
          h('button',{className:'btn btn-xs',onClick:function(){api('/cleanup-logs',{method:'POST'}).then(function(d){toast(d.cleaned.length?d.cleaned.join('; '):t('nothing_to_clean'))}).catch(function(er){toast(er.message,true)})}},t('cleanup_now')))))
  ];
  if(ss){
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t',style:{display:'flex',justifyContent:'space-between',alignItems:'center'}},
        h('span',null,t('vpn_settings')),
        h('button',{className:'btn btn-sm btn-p',onClick:function(){
          var payload=Object.assign({},vpn);
          payload.timeouts=Object.assign({},timeouts);
          payload.metrics=Object.assign({},metrics);
          payload.routing=Object.assign({},routing);
          api('/settings/vpn',{method:'PUT',body:JSON.stringify(payload)}).then(function(){_vpnEdits={};toast(t('settings_saved'));loadSettings()}).catch(function(er){toast(er.message,true)})}},t('save_vpn'))),
      h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'10px'}},t('apply_after_save')),
      h('div',{style:{display:'flex',gap:'12px',flexWrap:'wrap',marginBottom:'12px'}},
        settingText(vpn,'listen_address',t('listen_addr'),true),
        h('div',{style:{marginBottom:'8px'}},
          h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'3px'}},t('auth_code')),
          h('select',{className:'input',style:{padding:'4px 8px',fontSize:'12px'},value:String(vpn.auth_failure_status_code||407),onChange:function(e){vpn.auth_failure_status_code=parseInt(e.target.value);_vpnEdits.auth_failure_status_code=vpn.auth_failure_status_code}},
            h('option',{value:'407'},'407'),h('option',{value:'405'},'405')))),
      h('div',{style:{display:'flex',gap:'16px',flexWrap:'wrap',marginBottom:'14px'}},
        settingToggle(vpn,'ipv6_available',t('ipv6')),
        settingToggle(vpn,'allow_private_network_connections',t('allow_private')),
        settingToggle(vpn,'speedtest_enable',t('speedtest')),
        settingToggle(vpn,'ping_enable',t('ping'))),
      h('div',{style:{fontSize:'11px',fontWeight:'600',color:'var(--tx2)',marginBottom:'8px'}},'Timeouts'),
      h('div',{className:'grid grid3',style:{gap:'8px'}},
        settingNumber(timeouts,'tls_handshake',t('timeout_tls'),t('seconds'),1,120),
        settingNumber(timeouts,'client_listener',t('timeout_listener'),t('seconds'),1,600),
        settingNumber(timeouts,'connection',t('timeout_connect'),t('seconds'),1,120),
        settingNumber(timeouts,'tcp_idle',t('timeout_tcp'),t('seconds'),10,7200),
        settingNumber(timeouts,'udp_idle',t('timeout_udp'),t('seconds'),10,600))));
    var protoOpen=_settingsExpand.protocol;
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t',style:{cursor:'pointer'},onClick:function(){_settingsExpand.protocol=!_settingsExpand.protocol;R()}},
        h('span',null,(protoOpen?'\u25BC ':'\u25B6 ')+t('protocol_settings'))),
      protoOpen?h('div',{className:'grid grid2',style:{gap:'16px'}},
        h('div',null,
          h('div',{style:{fontSize:'11px',fontWeight:'600',color:'var(--tx2)',marginBottom:'8px'}},t('http2_settings')),
          settingNumber(http2,'max_concurrent_streams',t('max_streams'),null,1,1000),
          settingNumber(http2,'max_frame_size',t('frame_size'),null,16384,16777215),
          settingNumber(http2,'header_table_size',t('header_table'),null,0,65536),
          settingNumber(http2,'initial_connection_window_size',t('conn_window'),null,65535,2147483647),
          settingNumber(http2,'initial_stream_window_size',t('stream_window'),null,65535,2147483647)),
        h('div',null,
          h('div',{style:{fontSize:'11px',fontWeight:'600',color:'var(--tx2)',marginBottom:'8px'}},t('quic_settings')),
          settingNumber(quic,'max_concurrent_streams',t('max_streams'),null,1,1000),
          settingNumber(quic,'max_frame_size',t('frame_size'),null,16384,16777215),
          settingNumber(quic,'initial_connection_window_size',t('conn_window'),null,65535,2147483647),
          settingNumber(quic,'initial_stream_window_size',t('stream_window'),null,65535,2147483647))):null));
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t'},t('metrics_settings')),
      h('div',{style:{display:'flex',gap:'12px',flexWrap:'wrap'}},
        settingText(metrics,'address',t('metrics_addr'),true),
        settingNumber(metrics,'timeout',t('metrics_timeout'),t('seconds'),1,300))));
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t'},t('routing')),
      h('div',{style:{display:'flex',alignItems:'center',gap:'12px'}},
        h('button',{className:'btn btn-xs'+((!routing.socks5_address)?' btn-p':''),onClick:function(){if(!_vpnEdits._routing)_vpnEdits._routing={};_vpnEdits._routing.socks5_address='';R()}},t('direct')),
        h('button',{className:'btn btn-xs'+((routing.socks5_address)?' btn-p':''),onClick:function(){if(!_vpnEdits._routing)_vpnEdits._routing={};_vpnEdits._routing.socks5_address=routing.socks5_address||'127.0.0.1:1080';R()}},t('socks5')),
        routing.socks5_address?h('input',{className:'input',type:'text',style:{width:'200px',padding:'4px 8px',fontSize:'12px'},value:routing.socks5_address,onChange:function(e){if(!_vpnEdits._routing)_vpnEdits._routing={};_vpnEdits._routing.socks5_address=e.target.value;routing.socks5_address=e.target.value}}):null)));
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t',style:{display:'flex',justifyContent:'space-between',alignItems:'center'}},
        h('span',null,t('rules_settings')),
        h('div',{style:{display:'flex',gap:'6px'}},
          h('button',{className:'btn btn-xs',onClick:function(){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits.push({cidr:'',client_random:'',action:'deny'});R()}},t('add_rule')),
          h('button',{className:'btn btn-sm btn-p',onClick:function(){var payload=_rulesEdits||rules;api('/settings/rules',{method:'PUT',body:JSON.stringify({rules:payload})}).then(function(){_rulesEdits=null;toast(t('settings_saved'));loadSettings()}).catch(function(er){toast(er.message,true)})}},t('save_rules')))),
      rules.length?h('table',{className:'tbl'},
        h('thead',null,h('tr',null,h('th',null,t('cidr')),h('th',null,'Client Random'),h('th',null,t('action')),h('th',{style:{width:'60px'}},t('delete')))),
        h('tbody',null,rules.map(function(r,i){return h('tr',null,
          h('td',null,h('input',{className:'input',type:'text',style:{width:'100%',padding:'3px 6px',fontSize:'11px'},value:r.cidr||'',onChange:function(e){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits[i]=Object.assign({},_rulesEdits[i],{cidr:e.target.value})}})),
          h('td',null,h('input',{className:'input',type:'text',style:{width:'100%',padding:'3px 6px',fontSize:'11px'},value:r.client_random||'',onChange:function(e){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits[i]=Object.assign({},_rulesEdits[i],{client_random:e.target.value})}})),
          h('td',null,h('select',{className:'input',style:{padding:'3px 6px',fontSize:'11px'},value:r.action||'deny',onChange:function(e){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits[i]=Object.assign({},_rulesEdits[i],{action:e.target.value})}},h('option',{value:'allow'},t('allow')),h('option',{value:'deny'},t('deny')))),
          h('td',null,h('button',{className:'btn btn-xs btn-d',onClick:function(){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits.splice(i,1);R()}},'\u00D7')))}))):
        h('div',{style:{color:'var(--tx3)',fontSize:'12px',padding:'12px 0',textAlign:'center'}},t('no_conn_data'))));
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t'},t('tls_hosts')+' ('+t('read_only')+')'),
      hosts.length?h('table',{className:'tbl'},
        h('thead',null,h('tr',null,h('th',null,t('host_type')),h('th',null,t('hostname')),h('th',null,t('cert_path')))),
        h('tbody',null,hosts.map(function(ho){return h('tr',null,
          h('td',null,ho.type||''),
          h('td',null,ho.hostname||''),
          h('td',{style:{fontSize:'10px',color:'var(--tx3)',wordBreak:'break-all'}},ho.cert_path||''))}))):
        h('div',{style:{color:'var(--tx3)',fontSize:'12px',padding:'12px 0',textAlign:'center'}},'\u2014')));
  }
  var rawOpen=_settingsExpand.rawToml;
  sections.push(h('div',{className:'card'},
    h('div',{className:'card-t',style:{cursor:'pointer'},onClick:function(){_settingsExpand.rawToml=!_settingsExpand.rawToml;R()}},
      h('span',null,(rawOpen?'\u25BC ':'\u25B6 ')+t('raw_toml'))),
    rawOpen?h('div',null,
      h('div',{style:{marginBottom:'12px'}},
        h('div',{style:{fontSize:'11px',fontWeight:'600',color:'var(--tx2)',marginBottom:'6px'}},'vpn.toml'),
        va=h('textarea',{className:'input input-m',style:{minHeight:'200px'}},s.vpn_toml||''),
        h('button',{className:'btn btn-sm',style:{marginTop:'10px'},onClick:function(){saveCfg('vpn_toml',va.value)}},t('save'))),
      h('div',{style:{marginBottom:'12px'}},
        h('div',{style:{fontSize:'11px',fontWeight:'600',color:'var(--tx2)',marginBottom:'6px'}},'rules.toml'),
        ra=h('textarea',{className:'input input-m',style:{minHeight:'120px'}},s.rules_toml||''),
        h('button',{className:'btn btn-sm',style:{marginTop:'10px'},onClick:function(){saveCfg('rules_toml',ra.value)}},t('save'))),
      h('div',null,
        h('div',{style:{fontSize:'11px',fontWeight:'600',color:'var(--tx2)',marginBottom:'6px'}},'hosts.toml ('+t('read_only')+')'),
        h('div',{className:'cb'},s.hosts_toml||''))):null));
  return h('div',{className:'tab-content'},sections);
}

'''
