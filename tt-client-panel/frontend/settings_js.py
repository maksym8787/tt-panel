SETTINGS_JS = r'''async function loadSettings(){
  try{var r=await api('/settings');S.settings=r.settings||r||{}}
  catch(e){toast(e.message,true)}
  R()}

async function svcAct(a,btn){
  await withLoading(btn,async function(){
    try{
      var r=await api('/service/'+enc(a),{method:'POST'});
      if(r&&r.ok===false)throw new Error(r.error||t('svc_action_failed'));
      toast(t('service_label')+' '+a+' — '+t('svc_action_ok'));
      setTimeout(loadStatus,RELOAD_DELAY_MS)}
    catch(e){toast(e.message,true)}})}

function confirmSvcAct(a,btn){
  if(a==='restart'||a==='stop'){
    S.modal={t:'confirm',title:t('service_label')+': '+a,msg:t('svc_confirm_'+a),
      onOk:function(b){S.modal=null;R();svcAct(a,b)}};
    R();return}
  svcAct(a,btn)}

async function saveSettings(data,btn){
  await withLoading(btn,async function(){
    try{
      var r=await api('/settings',{method:'PUT',body:JSON.stringify(data)});
      S.settings=r.settings||data;
      clearDraft('set_');
      toast(t('saved'));R()}
    catch(e){toast(e.message,true)}})}

function renderSettings(){
  var cfg=S.settings;
  var dnsArr=Array.isArray(cfg.dns_upstreams)?cfg.dns_upstreams:[];
  var exclArr=Array.isArray(cfg.exclusions)?cfg.exclusions:[];
  if(S.draft.set_excl===undefined)S.draft.set_excl=exclArr.join('\n');
  return h('div',null,
    h('div',{className:'card'},
      h('div',{className:'card-t'},t('settings')),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},
          fl(t('health_interval'),'health'),
          dinput('set_hci',{className:'input input-m',id:'set-hci',type:'number',min:'10',max:'300',value:String(cfg.health_check_interval||30)})),
        h('div',{className:'fg'},
          fl(t('auto_failover'),'failover'),
          h('div',{style:{display:'flex',alignItems:'center',gap:'10px'}},
            h('label',{className:'toggle'},dcheck('set_afe',cfg.auto_failover!==false),h('span',{className:'slider'})),
            h('span',{style:{fontSize:'11px',color:'var(--tx3)'}},t('threshold')+':'),
            dinput('set_aft',{className:'input input-m',id:'set-aft',type:'number',min:'1',max:'10',value:String(cfg.failover_threshold||3),style:{width:'60px'}}),
            h('span',{style:{fontSize:'10px',color:'var(--tx3)'}},t('failures'))))),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},
          fl(t('vpn_mode'),'vpn_mode'),
          dselect('set_vpm',cfg.vpn_mode||'general',[{v:'general',l:t('general')},{v:'selective',l:t('selective')}])),
        h('div',{className:'fg'},
          fl(t('killswitch'),'killswitch'),
          h('div',{style:{display:'flex',alignItems:'center',gap:'10px'}},
            h('label',{className:'toggle'},dcheck('set_kse',cfg.killswitch_enabled!==false),h('span',{className:'slider'}))))),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},
          fl(t('activate_timeout'),'activate_timeout'),
          dinput('set_actt',{className:'input input-m',id:'set-actt',type:'number',min:'3',max:'30',value:String(cfg.activate_timeout||10)})),
        h('div',{className:'fg'},
          fl(t('failover_timeout'),'failover_timeout'),
          dinput('set_fot',{className:'input input-m',id:'set-fot',type:'number',min:'3',max:'15',value:String(cfg.failover_timeout||5)}))),
      h('div',{className:'grid grid2'},
        h('div',{className:'fg'},
          fl(t('dns'),'dns'),
          dinput('set_dns',{className:'input input-m',id:'set-dns',value:dnsArr.join(', '),placeholder:'8.8.8.8, 1.1.1.1'})),
        h('div',{className:'fg'},
          fl(t('mtu'),'mtu'),
          dinput('set_mtu',{className:'input input-m',id:'set-mtu',type:'number',min:'1200',max:'9000',value:String(cfg.mtu_size||1280)}))),
      h('div',{className:'fg'},
        fl(t('exclusions_label'),'exclusions'),
        h('textarea',{className:'input input-m',id:'set-excl',placeholder:'example.com\n10.0.0.0/8',style:{minHeight:'80px'},
          value:S.draft.set_excl,onInput:function(e){S.draft.set_excl=e.target.value}})),
      h('button',{className:'btn btn-p',onClick:function(e){
        var num=function(key,def,lo,hi){var v=parseInt(dval(key),10);if(isNaN(v))return def;return Math.max(lo,Math.min(v,hi))};
        saveSettings({
          health_check_interval:num('set_hci',30,10,300),
          auto_failover:!!S.draft.set_afe,
          failover_threshold:num('set_aft',3,1,10),
          vpn_mode:dval('set_vpm')||'general',
          killswitch_enabled:!!S.draft.set_kse,
          dns_upstreams:splitAddresses(dval('set_dns')),
          mtu_size:num('set_mtu',1280,1200,9000),
          activate_timeout:num('set_actt',10,3,30),
          failover_timeout:num('set_fot',5,3,15),
          exclusions:String(S.draft.set_excl||'').split('\n').map(function(s){return s.trim()}).filter(Boolean)
        },e.currentTarget)}},t('save'))));
}
'''
