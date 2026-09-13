INIT_JS = r'''var _refreshTimer=null,_refreshing=false;

function startRefresh(){
  stopRefresh();
  _refreshTimer=setInterval(async function(){
    if(_refreshing||!S.auth)return;
    if(S.tab!=='servers'&&S.tab!=='monitor')return;
    _refreshing=true;
    try{
      var prev=S._prevOnBackup;
      await loadStatus();
      S._prevOnBackup=S.status&&S.status.on_backup;
      if(S.status&&S.status.on_backup&&!prev)await loadServers();
      if(S.tab==='monitor'){await loadNetHistory();await loadServerLatency()}
      Rbg(function(){if(S.tab==='monitor'){drawNetChart();drawLatencyChart()}});
    }finally{_refreshing=false}
  },POLL_MS)}

function stopRefresh(){if(_refreshTimer){clearInterval(_refreshTimer);_refreshTimer=null}}

document.addEventListener('keydown',function(e){if(e.key==='Escape'&&S.modal){clearDraft('m_');S.modal=null;R()}});
document.addEventListener('visibilitychange',function(){
  if(document.visibilityState==='hidden'){stopRefresh()}
  else if(S.auth){startRefresh()}});

applyTheme();
checkAuth();
'''
