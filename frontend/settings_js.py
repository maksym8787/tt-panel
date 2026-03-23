SETTINGS_JS = r'''
var _vpnEdits={};
var _rulesEdits=null;
var _settingsExpand={protocol:false,rawToml:false};
function tip(key){var text=t('tip_'+key);if(!text||text===('tip_'+key))return null;
  var wrap=h('span',{className:'tip-wrap',style:{position:'relative',display:'inline-flex',marginLeft:'4px'}});
  var icon=h('span',{style:{cursor:'help',fontSize:'11px',color:'var(--ac)',display:'inline-flex',alignItems:'center',justifyContent:'center',width:'16px',height:'16px',borderRadius:'50%',border:'1px solid var(--ac)',flexShrink:'0',fontStyle:'normal',fontWeight:'700',lineHeight:'1'}},'i');
  var popup=h('div',{style:{display:'none',position:'absolute',bottom:'22px',left:'50%',transform:'translateX(-50%)',background:'var(--sf2)',border:'1px solid var(--bd)',borderRadius:'6px',padding:'8px 10px',fontSize:'11px',color:'var(--tx)',width:'220px',zIndex:'1000',boxShadow:'0 4px 12px rgba(0,0,0,.3)',lineHeight:'1.4',whiteSpace:'normal'}},text);
  icon.addEventListener('mouseenter',function(){popup.style.display='block'});
  icon.addEventListener('mouseleave',function(){popup.style.display='none'});
  icon.addEventListener('touchstart',function(e){e.preventDefault();popup.style.display=popup.style.display==='none'?'block':'none'});
  wrap.appendChild(icon);wrap.appendChild(popup);return wrap}
function _setVpnEdit(section,key,val){
  if(section){if(!_vpnEdits[section])_vpnEdits[section]={};_vpnEdits[section][key]=val}else{_vpnEdits[key]=val}
}
function settingToggle(obj,key,label,tipKey,section){
  return h('div',{style:{display:'flex',alignItems:'center',gap:'6px'}},
    h('button',{className:'btn btn-xs'+(obj[key]?' btn-p':''),style:{minWidth:'40px'},onClick:function(){obj[key]=!obj[key];_setVpnEdit(section,key,obj[key]);R()}},obj[key]?'ON':'OFF'),
    h('span',{style:{fontSize:'11px',color:'var(--tx2)'}},label),
    tipKey?tip(tipKey):null)
}
function settingNumber(obj,key,label,suffix,min,max,tipKey,section){
  return h('div',{style:{marginBottom:'8px'}},
    h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'3px',display:'flex',alignItems:'center'}},label,tipKey?tip(tipKey):null),
    h('div',{style:{display:'flex',alignItems:'center',gap:'4px'}},
      h('input',{className:'input',type:'number',min:String(min||0),max:String(max||999999999),style:{width:'100px',padding:'4px 8px',fontSize:'12px'},value:String(obj[key]!=null?obj[key]:0),onInput:function(e){var v=parseInt(e.target.value);if(isNaN(v))return;obj[key]=v;_setVpnEdit(section,key,v)}}),
      suffix?h('span',{style:{fontSize:'10px',color:'var(--tx3)'}},suffix):null))
}
function settingText(obj,key,label,wide,tipKey,section){
  return h('div',{style:{marginBottom:'8px',flex:wide?'1':'none'}},
    h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'3px',display:'flex',alignItems:'center'}},label,tipKey?tip(tipKey):null),
    h('input',{className:'input',type:'text',style:{width:wide?'100%':'200px',padding:'4px 8px',fontSize:'12px'},value:String(obj[key]||''),onInput:function(e){obj[key]=e.target.value;_setVpnEdit(section,key,e.target.value)}}))
}
function renderSettings(){
  var s=S.settings;if(!s.vpn_toml&&s.vpn_toml!==''){loadSettings();return h('div',{className:'tab-content'},h('div',{className:'skeleton skel-card'}),h('div',{className:'skeleton skel-card'}))}
  var va,ra;var ps=S.panelSettings||{};
  var ttlOpts=[{v:300,l:'5 '+t('minutes')},{v:900,l:'15 '+t('minutes')},{v:1800,l:'30 '+t('minutes')},{v:3600,l:'1h'},{v:14400,l:'4h'},{v:43200,l:'12h'},{v:86400,l:'24h'}];
  var renewOn=ps.auto_renew_enabled!==false;
  var ss=S.structuredSettings;
  var vpnData=ss&&ss.vpn?ss.vpn:{};
  var vpn=Object.assign({},vpnData.core||{},_vpnEdits);
  var http2=Object.assign({},vpnData.http2||{},_vpnEdits._http2||{});
  var quic=Object.assign({},vpnData.quic||{},_vpnEdits._quic||{});
  var metrics=Object.assign({},vpnData.metrics||{},_vpnEdits._metrics||{});
  var forward=_vpnEdits._forward||(vpnData.forward||'direct');
  var socks5Addr=_vpnEdits._socks5_address!=null?_vpnEdits._socks5_address:(vpnData.socks5_address||'');
  var rules=ss&&ss.rules?ss.rules.slice():[];
  if(_rulesEdits)rules=_rulesEdits;
  var hostsData=ss&&ss.hosts?ss.hosts:{};
  var allHosts=[].concat(
    (hostsData.main_hosts||[]).map(function(h){return Object.assign({type:'main'},h)}),
    (hostsData.reverse_proxy_hosts||[]).map(function(h){return Object.assign({type:'reverse_proxy'},h)}));
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
          var payload={core:Object.assign({},vpn),http2:Object.assign({},http2),quic:Object.assign({},quic),metrics:Object.assign({},metrics),forward:forward,socks5_address:socks5Addr};
          api('/settings/vpn',{method:'PUT',body:JSON.stringify(payload)}).then(function(){_vpnEdits={};toast(t('settings_saved'));loadSettings()}).catch(function(er){toast(er.message,true)})}},t('save_vpn'))),
      h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'10px'}},t('apply_after_save')),
      h('div',{style:{display:'flex',gap:'12px',flexWrap:'wrap',marginBottom:'12px'}},
        settingText(vpn,'listen_address',t('listen_addr'),true,'listen_address'),
        h('div',{style:{marginBottom:'8px'}},
          h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginBottom:'3px'}},t('auth_code')),
          h('select',{className:'input',style:{padding:'4px 8px',fontSize:'12px'},value:String(vpn.auth_failure_status_code||407),onChange:function(e){vpn.auth_failure_status_code=parseInt(e.target.value);_vpnEdits.auth_failure_status_code=vpn.auth_failure_status_code}},
            h('option',{value:'407'},'407'),h('option',{value:'405'},'405')))),
      h('div',{style:{display:'flex',gap:'16px',flexWrap:'wrap',marginBottom:'14px'}},
        settingToggle(vpn,'ipv6_available',t('ipv6'),'ipv6_available',null),
        settingToggle(vpn,'allow_private_network_connections',t('allow_private'),'allow_private',null),
        settingToggle(vpn,'speedtest_enable',t('speedtest'),'speedtest',null),
        settingToggle(vpn,'ping_enable',t('ping'),'ping',null)),
      h('div',{style:{fontSize:'11px',fontWeight:'600',color:'var(--tx2)',marginBottom:'8px'}},'Timeouts'),
      h('div',{className:'grid grid3',style:{gap:'8px'}},
        settingNumber(vpn,'tls_handshake_timeout_secs',t('timeout_tls'),t('seconds'),1,120,'timeout_tls',null),
        settingNumber(vpn,'client_listener_timeout_secs',t('timeout_listener'),t('seconds'),10,86400,'timeout_listener',null),
        settingNumber(vpn,'connection_establishment_timeout_secs',t('timeout_connect'),t('seconds'),1,300,'timeout_connect',null),
        settingNumber(vpn,'tcp_connections_timeout_secs',t('timeout_tcp'),t('seconds'),60,2592000,'timeout_tcp',null),
        settingNumber(vpn,'udp_connections_timeout_secs',t('timeout_udp'),t('seconds'),10,86400,'timeout_udp',null))));
    var protoOpen=_settingsExpand.protocol;
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t',style:{cursor:'pointer'},onClick:function(){_settingsExpand.protocol=!_settingsExpand.protocol;R()}},
        h('span',null,(protoOpen?'\u25BC ':'\u25B6 ')+t('protocol_settings'))),
      protoOpen?h('div',{className:'grid grid2',style:{gap:'16px'}},
        h('div',null,
          h('div',{style:{fontSize:'11px',fontWeight:'600',color:'var(--tx2)',marginBottom:'8px'}},t('http2_settings')),
          settingNumber(http2,'max_concurrent_streams',t('max_streams'),null,1,100000,'max_streams','_http2'),
          settingNumber(http2,'max_frame_size',t('frame_size'),null,16384,16777215,'frame_size','_http2'),
          settingNumber(http2,'header_table_size',t('header_table'),null,0,1048576,'header_table','_http2'),
          settingNumber(http2,'initial_connection_window_size',t('conn_window'),null,65535,2147483647,'conn_window','_http2'),
          settingNumber(http2,'initial_stream_window_size',t('stream_window'),null,65535,2147483647,'stream_window','_http2')),
        h('div',null,
          h('div',{style:{fontSize:'11px',fontWeight:'600',color:'var(--tx2)',marginBottom:'8px'}},t('quic_settings')),
          settingNumber(quic,'initial_max_streams_bidi',t('max_streams')+' (bidi)',null,1,100000,'max_streams','_quic'),
          settingNumber(quic,'initial_max_streams_uni',t('max_streams')+' (uni)',null,1,100000,'max_streams','_quic'),
          settingNumber(quic,'recv_udp_payload_size','Recv payload',null,1200,65535,null,'_quic'),
          settingNumber(quic,'send_udp_payload_size','Send payload',null,1200,65535,null,'_quic'),
          settingNumber(quic,'initial_max_data',t('conn_window'),null,1048576,1073741824,'conn_window','_quic'))):null));
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t'},t('metrics_settings')),
      h('div',{style:{display:'flex',gap:'12px',flexWrap:'wrap'}},
        settingText(metrics,'address',t('metrics_addr'),true,'metrics_addr','_metrics'),
        settingNumber(metrics,'request_timeout_secs',t('metrics_timeout'),t('seconds'),1,60,'metrics_timeout','_metrics'))));
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t'},t('routing')),
      h('div',{style:{display:'flex',alignItems:'center',gap:'12px'}},
        h('button',{className:'btn btn-xs'+((forward==='direct')?' btn-p':''),onClick:function(){_vpnEdits._forward='direct';_vpnEdits._socks5_address='';R()}},t('direct')),
        h('button',{className:'btn btn-xs'+((forward==='socks5')?' btn-p':''),onClick:function(){_vpnEdits._forward='socks5';_vpnEdits._socks5_address=socks5Addr||'127.0.0.1:1080';R();}},t('socks5')),
        forward==='socks5'?h('input',{className:'input',type:'text',style:{width:'200px',padding:'4px 8px',fontSize:'12px'},value:socks5Addr,onChange:function(e){_vpnEdits._socks5_address=e.target.value}}):null)));
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t',style:{display:'flex',justifyContent:'space-between',alignItems:'center'}},
        h('span',null,t('rules_settings')),
        h('div',{style:{display:'flex',gap:'6px'}},
          h('button',{className:'btn btn-xs',onClick:function(){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits.push({cidr:'',client_random_prefix:'',action:'deny'});R()}},t('add_rule')),
          h('button',{className:'btn btn-sm btn-p',onClick:function(){var payload=_rulesEdits||rules;api('/settings/rules',{method:'PUT',body:JSON.stringify({rules:payload})}).then(function(){_rulesEdits=null;toast(t('settings_saved'));loadSettings()}).catch(function(er){toast(er.message,true)})}},t('save_rules')))),
      rules.length?h('table',{className:'tbl'},
        h('thead',null,h('tr',null,h('th',null,t('cidr')),h('th',null,'Client Random'),h('th',null,t('action')),h('th',{style:{width:'60px'}},t('delete')))),
        h('tbody',null,rules.map(function(r,i){return h('tr',null,
          h('td',null,h('input',{className:'input',type:'text',style:{width:'100%',padding:'3px 6px',fontSize:'11px'},value:r.cidr||'',onChange:function(e){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits[i]=Object.assign({},_rulesEdits[i],{cidr:e.target.value})}})),
          h('td',null,h('input',{className:'input',type:'text',style:{width:'100%',padding:'3px 6px',fontSize:'11px'},value:r.client_random_prefix||'',onChange:function(e){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits[i]=Object.assign({},_rulesEdits[i],{client_random_prefix:e.target.value})}})),
          h('td',null,h('select',{className:'input',style:{padding:'3px 6px',fontSize:'11px'},value:r.action||'deny',onChange:function(e){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits[i]=Object.assign({},_rulesEdits[i],{action:e.target.value})}},h('option',{value:'allow'},t('allow')),h('option',{value:'deny'},t('deny')))),
          h('td',null,h('button',{className:'btn btn-xs btn-d',onClick:function(){if(!_rulesEdits)_rulesEdits=rules.slice();_rulesEdits.splice(i,1);R()}},'\u00D7')))}))):
        h('div',{style:{color:'var(--tx3)',fontSize:'12px',padding:'12px 0',textAlign:'center'}},t('no_conn_data'))));
    sections.push(h('div',{className:'card'},
      h('div',{className:'card-t'},t('tls_hosts')+' ('+t('read_only')+')'),
      allHosts.length?h('table',{className:'tbl'},
        h('thead',null,h('tr',null,h('th',null,t('host_type')),h('th',null,t('hostname')),h('th',null,t('cert_path')))),
        h('tbody',null,allHosts.map(function(ho){return h('tr',null,
          h('td',null,ho.type||''),
          h('td',null,ho.hostname||''),
          h('td',{style:{fontSize:'10px',color:'var(--tx3)',wordBreak:'break-all'}},ho.cert_chain_path||''))}))):
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
