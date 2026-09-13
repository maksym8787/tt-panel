SERVERS_JS = r'''async function loadAll(){await Promise.all([loadServers(),loadStatus()]);R()}
async function loadServers(){try{var r=await api('/servers');S.servers=r.servers||[];S.activeServerId=r.active_server_id||''}catch(e){toast(e.message,true)}}
async function loadStatus(){
  try{
    S.status=await api('/status');
    // Keep the Active badge in sync even on a backup→backup failover.
    if(S.status&&S.status.active_server_id!==undefined&&S.status.active_server_id!==S.activeServerId){
      S.activeServerId=S.status.active_server_id;
      loadServers();
    }
    S.staleTicks=0;
  }catch(e){S.staleTicks++}}

async function addServer(data,btn){
  await withLoading(btn,async function(){
    try{
      await api('/servers',{method:'POST',body:JSON.stringify(data)});
      toast(t('server_added'));
      clearDraft('add_');
      await loadAll();R()}
    catch(e){toast(e.message,true)}})}

async function deleteServer(id){
  var isActive=id===S.activeServerId;
  S.modal={t:'confirm',title:t('delete'),
    msg:isActive?t('delete_active_confirm'):t('delete_confirm'),
    onOk:async function(btn){await withLoading(btn,async function(){
      try{await api('/servers/'+enc(id),{method:'DELETE'});toast(t('server_deleted'));S.modal=null;await loadAll();R()}
      catch(e){toast(e.message,true)}})}};
  R()}

async function activateServer(id,btn){
  await withLoading(btn,async function(){
    try{
      var r=await api('/servers/'+enc(id)+'/activate',{method:'POST'});
      toast(r.ok?(r.message||t('activation_ok')):(r.error||t('activation_fail')),!r.ok);
      await loadAll();R()}
    catch(e){toast(e.message,true)}})}

async function editServer(id,data,btn){
  await withLoading(btn,async function(){
    try{
      var r=await api('/servers/'+enc(id),{method:'PUT',body:JSON.stringify(data)});
      if(r&&r.server&&r.server.restart_error)toast(t('restart_failed')+': '+r.server.restart_error,true);
      else toast(t('saved'));
      clearDraft('m_');S.modal=null;
      await loadAll();R()}
    catch(e){toast(e.message,true)}})}

function renderStatusBar(){
  var st=S.status;var hl=st&&st.health?st.health:{};var ok=hl.connected;var srv=st&&st.active_server;
  var stale=S.staleTicks>=3;
  return h('div',{className:'status-bar'},
    h('span',{className:'dot '+(stale?'dot-off':(ok?'dot-on':'dot-off'))}),
    h('span',{style:{fontWeight:600}},stale?t('status_stale'):(ok?t('connected')+(srv?' — '+srv.name:''):t('disconnected'))),
    (!stale&&hl.latency_ms)?h('span',{style:{color:'var(--tx3)',fontSize:'12px',fontFamily:'var(--m)',marginLeft:'auto'}},t('latency')+': '+hl.latency_ms+'ms'):'',
    (!stale&&hl.external_ip)?h('span',{style:{color:'var(--tx3)',fontSize:'12px',fontFamily:'var(--m)'}},t('external_ip')+': '+hl.external_ip):'');
}

function renderServers(){
  var sorted=S.servers.slice().sort(function(a,b){return(a.priority||0)-(b.priority||0)});
  var onBackup=false;
  if(S.activeServerId&&sorted.length>1&&sorted[0].enabled&&sorted[0].id!==S.activeServerId)onBackup=true;
  return h('div',null,
    renderStatusBar(),
    onBackup?h('div',{style:{background:'var(--orbg)',border:'1px solid rgba(245,158,11,.25)',borderRadius:'var(--r2)',padding:'10px 16px',marginBottom:'10px',fontSize:'12px',color:'var(--or)',display:'flex',alignItems:'center',gap:'8px'}},
      '⚠ '+t('on_backup_server'),
      h('button',{className:'btn btn-xs btn-p',onClick:function(e){activateServer(sorted[0].id,e.currentTarget)}},t('switch_to_primary'))):null,
    sorted.length===0?h('div',{className:'card',style:{textAlign:'center',padding:'40px',color:'var(--tx3)'}},t('no_servers')):sorted.map(function(s,i){
      var isActive=s.id===S.activeServerId;
      return h('div',{className:'sc'+(isActive?' sc-active':'')+(!s.enabled?' sc-dis':'')},
        h('div',{style:{display:'flex',flexDirection:'column',gap:'2px',marginRight:'10px',alignItems:'center'}},
          h('span',{style:{fontSize:'10px',color:'var(--tx3)',fontFamily:'var(--m)'}},''+(i+1)),
          h('button',{className:'btn btn-xs','aria-label':t('move_up'),disabled:i===0||_reordering,onClick:function(e){moveServer(i,-1,e.currentTarget)}},'▲'),
          h('button',{className:'btn btn-xs','aria-label':t('move_down'),disabled:i===sorted.length-1||_reordering,onClick:function(e){moveServer(i,1,e.currentTarget)}},'▼')),
        h('div',{className:'sc-info'},
          h('div',{style:{display:'flex',alignItems:'center',gap:'8px'}},
            h('span',{className:'sc-name'},s.name||s.hostname),
            isActive?h('span',{className:'badge b-gn'},t('active')):'',
            !s.enabled?h('span',{className:'badge b-rd'},t('disabled')):'',
            s.upstream_protocol?h('span',{className:'badge b-bl'},s.upstream_protocol):''),
          h('div',{className:'sc-host'},s.hostname+(s.addresses&&s.addresses.length?' — '+(Array.isArray(s.addresses)?s.addresses.join(', '):s.addresses):''))),
        h('div',{className:'sc-acts'},
          !isActive?h('button',{className:'btn btn-sm btn-p',onClick:function(e){activateServer(s.id,e.currentTarget)}},t('activate')):'',
          h('button',{className:'btn btn-sm',onClick:function(){clearDraft('m_');S.modal={t:'edit',s:s};R()}},t('edit')),
          h('button',{className:'btn btn-sm btn-d',onClick:function(){deleteServer(s.id)}},t('delete'))));
    }),
    renderAddServer());
}

// Serialised: parallel reorder requests could otherwise be applied out of order.
var _reordering=false;
function moveServer(idx,dir,btn){
  if(_reordering)return;
  var sorted=S.servers.slice().sort(function(a,b){return(a.priority||0)-(b.priority||0)});
  var ni=idx+dir;if(ni<0||ni>=sorted.length)return;
  var becomesPrimary=(ni===0||idx===0);

  var apply=function(){
    var tmp=sorted[idx];sorted[idx]=sorted[ni];sorted[ni]=tmp;
    sorted.forEach(function(s,i){s.priority=i+1});
    S.servers=sorted;
    _reordering=true;R();
    api('/servers/reorder',{method:'PUT',body:JSON.stringify({order:sorted.map(function(s){return s.id})})})
      .then(function(r){
        if(r&&r.activated)toast(t('activation_ok'));
        else if(r&&r.ok===false)toast(r.error||t('activation_fail'),true);
      })
      .catch(function(e){toast(e.message,true)})
      .finally(function(){
        setTimeout(function(){_reordering=false;loadAll()},RELOAD_DELAY_MS)});
  };

  // Changing the first slot reconnects the VPN — ask first.
  if(becomesPrimary&&S.servers.length>1){
    S.modal={t:'confirm',title:t('switch_to_primary'),msg:t('reorder_primary_confirm'),
      onOk:function(){S.modal=null;R();apply()}};
    R();return}
  apply()}

function renderAddServer(){
  return h('div',{className:'card'},
    h('div',{className:'card-t'},t('add_server')),
    h('div',{className:'add-tabs'},
      h('button',{className:'add-tab'+(S.addMode==='deeplink'?' on':''),onClick:function(){S.addMode='deeplink';R()}},t('deeplink')),
      h('button',{className:'add-tab'+(S.addMode==='manual'?' on':''),onClick:function(){S.addMode='manual';R()}},t('manual'))),
    S.addMode==='deeplink'?h('div',null,
      h('div',{className:'fg'},fl('Deeplink','deeplink'),
        dinput('add_dl',{className:'input input-m',id:'add-dl',placeholder:t('paste_deeplink')})),
      h('button',{className:'btn btn-p',onClick:function(e){
        var v=dval('add_dl').trim();
        if(!v){toast(t('paste_deeplink'),true);return}
        if(v.indexOf('tt://')!==0){toast(t('deeplink_prefix_error'),true);return}
        addServer({deeplink:v},e.currentTarget)}},t('add_server'))
    ):h('div',null,
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},fl(t('name'),'srv_name'),dinput('add_name',{className:'input',id:'add-name'})),
        h('div',{className:'fg'},fl(t('hostname'),'srv_hostname'),dinput('add_host',{className:'input input-m',id:'add-host',placeholder:'vpn.example.com'}))),
      h('div',{className:'fg'},fl(t('address'),'srv_address'),dinput('add_addr',{className:'input input-m',id:'add-addr',placeholder:'vpn.example.com:443'})),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},fl(t('username'),'srv_username'),dinput('add_user',{className:'input',id:'add-user',autocomplete:'off'})),
        h('div',{className:'fg'},fl(t('password'),'srv_password'),dinput('add_pass',{className:'input',id:'add-pass',type:'password',autocomplete:'new-password'}))),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},fl(t('protocol'),'srv_protocol'),dselect('add_proto','http2',[{v:'http2',l:'HTTP/2'},{v:'http3',l:'HTTP/3'}])),
        h('div',{className:'fg'},fl('SNI','srv_sni'),dinput('add_sni',{className:'input input-m',id:'add-sni',placeholder:t('hostname')}))),
      h('div',{style:{display:'flex',gap:'16px',marginBottom:'14px'}},
        h('label',{style:{display:'flex',alignItems:'center',gap:'6px',fontSize:'12px',cursor:'pointer'}},dcheck('add_ipv6',true),'IPv6'),
        h('label',{style:{display:'flex',alignItems:'center',gap:'6px',fontSize:'12px',cursor:'pointer'}},dcheck('add_dpi',false),'Anti-DPI')),
      h('button',{className:'btn btn-p',onClick:function(e){
        var host=dval('add_host').trim();
        if(!host){toast(t('hostname')+': '+t('required'),true);return}
        // Same comma-splitting as the edit dialog, matching the field hint.
        var addrs=splitAddresses(dval('add_addr'));
        if(!addrs.length)addrs=[host+':443'];
        addServer({hostname:host,addresses:addrs,username:dval('add_user'),password:dval('add_pass'),
          name:dval('add_name')||host,upstream_protocol:dval('add_proto'),custom_sni:dval('add_sni'),
          has_ipv6:!!S.draft.add_ipv6,anti_dpi:!!S.draft.add_dpi},e.currentTarget)}},t('add_server'))));
}
'''
