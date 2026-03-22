USERS_JS = r'''
function sortUsers(list){
  var s=S.userSort;var sorted=list.slice();
  sorted.sort(function(a,b){
    if(s==='name_asc')return a.username.localeCompare(b.username);
    if(s==='name_desc')return b.username.localeCompare(a.username);
    if(s==='date_new'){var d=(b.created_at||'').localeCompare(a.created_at||'');return d!==0?d:a.username.localeCompare(b.username)}
    if(s==='date_old'){var d=(a.created_at||'').localeCompare(b.created_at||'');return d!==0?d:a.username.localeCompare(b.username)}
    return 0});
  return sorted}
function renderUsers(){
  var aips=Object.keys(S.activeIps||{});
  var aipCount=aips.length;
  var filtered=S.users;
  if(S.userFilter){var f=S.userFilter.toLowerCase();filtered=S.users.filter(function(u){return u.username.toLowerCase().indexOf(f)!==-1})}
  filtered=sortUsers(filtered);
  var sortOpts=[{v:'name_asc',l:t('sort_name_az')},{v:'name_desc',l:t('sort_name_za')},{v:'date_new',l:t('sort_date_new')},{v:'date_old',l:t('sort_date_old')}];
  return h('div',{className:'tab-content'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'16px',gap:'12px',flexWrap:'wrap'}},
      h('div',{style:{fontSize:'13px',fontWeight:'600'}},S.users.length+' '+(S.users.length!==1?t('users_pl'):t('user'))),
      h('div',{className:'bg',style:{flex:'1',justifyContent:'flex-end'}},
        h('select',{className:'input',style:{maxWidth:'160px',padding:'6px 8px',fontSize:'11px'},value:S.userSort,onChange:function(e){S.userSort=e.target.value;R()}},sortOpts.map(function(o){return h('option',{value:o.v},o.l)})),
        h('input',{className:'input',placeholder:t('search_users'),style:{maxWidth:'200px',padding:'6px 12px',fontSize:'12px'},id:'user-search',value:S.userFilter||'',onInput:function(e){S.userFilter=e.target.value;R()}}),
        h('button',{className:'btn btn-p btn-sm',onClick:function(){S.modal={t:'add'};R()}},t('add_user')),
        h('button',{className:'btn btn-sm',onClick:function(){window.location.href=A+'/users/export'}},t('export_csv')),
        h('button',{className:'btn btn-sm',onClick:function(){var inp=document.createElement('input');inp.type='file';inp.accept='.csv';inp.onchange=function(){if(!inp.files[0])return;var rd=new FileReader();rd.onload=function(){api('/users/import',{method:'POST',body:JSON.stringify({csv:rd.result})}).then(function(d){toast(t('import_success').replace('{count}',d.count||0));loadDash()}).catch(function(e){toast(t('import_error')+': '+e.message,true)})};rd.readAsText(inp.files[0])};inp.click()}},t('import_csv')))),
    aipCount?h('div',{className:'card',style:{marginBottom:'14px'}},
      h('div',{className:'card-t'},h('span',null,aipCount+' '+(aipCount!==1?t('active_ips'):t('active_ip')))),
      h('div',{style:{display:'flex',flexWrap:'wrap',gap:'8px'}},aips.map(function(ip){
        var info=S.activeIps[ip];
        return h('div',{className:'badge b-gn',style:{fontSize:'11px',padding:'4px 10px'}},
          h('span',{className:'dot dot-on',style:{width:'6px',height:'6px'}}),ip+' ('+info.connections+' '+t('conn')+', '+ago(info.last_seen)+')')}))):null,
    h('div',{id:'user-list'},filtered.map(function(u){return renderUserCard(u)})));
}
function renderUserCard(u){var dis=u.enabled===false;var created=u.created_at?u.created_at.replace('T',' ').substring(0,16):'';var uNote=S.userNotes[u.username];
  return h('div',{className:'uc'+(dis?' uc-dis':'')},
  h('div',{className:'ui'},
    h('div',{className:'ua'+(dis?' ua-dis':'')},u.username[0].toUpperCase()),
    h('div',null,
      h('div',{style:{display:'flex',alignItems:'center',gap:'6px'}},
        h('span',{className:'un'+(dis?' un-dis':'')},u.username),
        dis?h('span',{className:'badge b-rd',style:{fontSize:'9px'}},t('user_disabled')):null),
      created?h('div',{style:{fontSize:'10px',color:'var(--tx3)',marginTop:'1px'}},t('created_label')+': '+created):null,
      h('div',{style:{display:'flex',alignItems:'center',gap:'4px',marginTop:'3px',cursor:'pointer'},title:t('note'),onClick:function(){var txt=prompt(t('note_placeholder'),uNote||'');if(txt!==null){api('/users/'+u.username+'/note',{method:'PUT',body:JSON.stringify({note:txt})}).then(function(){S.userNotes[u.username]=txt||undefined;if(!txt)delete S.userNotes[u.username];toast(t('note_saved'));R()}).catch(function(e){toast(e.message,true)})}}},
        h('span',{style:{fontSize:'11px',color:'var(--tx3)'}},'\u270F\uFE0F'),
        h('span',{style:{fontSize:'10px',color:uNote?'var(--tx2)':'var(--tx3)',fontStyle:'italic'}},uNote||t('note_placeholder'))),
      u.password?h('div',{style:{display:'flex',alignItems:'center',gap:'6px',marginTop:'2px'}},
        h('span',{className:'up',style:{cursor:'pointer'},title:t('password'),onClick:function(e){var sp=e.target;if(sp.textContent==='\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'){sp.textContent=u.password}else{sp.textContent='\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'}}},'\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'),
        h('span',{style:{cursor:'pointer',fontSize:'12px',color:'var(--tx3)',padding:'2px 4px',borderRadius:'4px',border:'1px solid var(--bd)'},title:t('copy'),onClick:function(){copyPassword(u.password)}},'\u{1F4CB}')):null)),
  h('div',{className:'uact'},
    h('button',{className:'btn btn-xs',onClick:function(){showCfg(u.username,'toml')}},t('btn_config')),
    h('button',{className:'btn btn-xs',onClick:function(){showCfg(u.username,'deeplink')}},t('btn_qr')),
    h('button',{className:'btn btn-xs',onClick:function(){chgPass(u.username)}},t('btn_pass')),
    h('button',{className:'btn btn-xs'+(dis?' btn-p':''),onClick:function(e){toggleUser(u.username,e.target)}},dis?t('btn_enable'):t('btn_disable')),
    h('button',{className:'btn btn-xs btn-d',onClick:function(){deleteUser(u.username)}},t('btn_del'))))}

'''
