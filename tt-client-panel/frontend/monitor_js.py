MONITOR_JS = r'''function srvName(id){
  if(!id)return '\u2014';
  for(var i=0;i<S.servers.length;i++){if(S.servers[i].id===id)return S.servers[i].name||S.servers[i].hostname||id}
  return id}
function failReason(r){
  if(!r)return '';
  var m=/^health_check_failed_(\d+)x$/.exec(r);
  return m?t('reason_health_failed').replace('{n}',m[1]):r}
async function loadNetHistory(hrs){hrs=hrs||S.netPeriod||1;S.netPeriod=hrs;try{var r=await api('/net-history?hours='+hrs);S.netHistory=r.history||[]}catch(e){}}
async function loadFailoverLog(){try{var r=await api('/failover-log');S.failoverLog=r.log||[]}catch(e){toast(e.message,true)}R()}
function fmtBps(b){if(!b||b<0)return '0 B/s';if(b>=1073741824)return(b/1073741824).toFixed(1)+' GB/s';if(b>=1048576)return(b/1048576).toFixed(1)+' MB/s';if(b>=1024)return(b/1024).toFixed(0)+' KB/s';return b+' B/s'}
var _netChart=null;
function drawNetChart(){
  if(typeof Chart==='undefined')return;
  var canvas=document.getElementById('net-chart');
  if(!canvas)return;
  var data=S.netHistory||[];
  if(!data.length){if(_netChart){try{_netChart.destroy()}catch(e){}_netChart=null}return}
  var labels=data.map(function(d){var dt=new Date(d.ts*1000);return String(dt.getHours()).padStart(2,'0')+':'+String(dt.getMinutes()).padStart(2,'0')});
  var rxData=data.map(function(d){return d.rx_bps||0});
  var txData=data.map(function(d){return d.tx_bps||0});
  var isDark=getComputedStyle(document.documentElement).getPropertyValue('--bg').trim().startsWith('#0');
  var gridColor=isDark?'rgba(255,255,255,.06)':'rgba(0,0,0,.06)';
  var tickColor=isDark?'rgba(255,255,255,.4)':'rgba(0,0,0,.4)';
  if(_netChart){try{if(_netChart.canvas!==canvas){_netChart.destroy();_netChart=null}else{_netChart.data.labels=labels;_netChart.data.datasets[0].data=rxData;_netChart.data.datasets[1].data=txData;_netChart.update('none');return}}catch(e){_netChart=null}}
  _netChart=new Chart(canvas,{type:'line',data:{labels:labels,datasets:[
    {label:t('download'),data:rxData,borderColor:'#22c55e',backgroundColor:'rgba(34,197,94,.08)',borderWidth:1.5,fill:true,tension:0.3,pointRadius:0,pointHitRadius:8},
    {label:t('upload'),data:txData,borderColor:'#f59e0b',backgroundColor:'rgba(245,158,11,.06)',borderWidth:1.5,fill:true,tension:0.3,pointRadius:0,pointHitRadius:8}
  ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,position:'top',labels:{color:tickColor,font:{size:10,family:'system-ui,sans-serif'},boxWidth:10,padding:8}},tooltip:{callbacks:{label:function(c){return c.dataset.label+': '+fmtBps(c.raw)}}}},scales:{x:{ticks:{color:tickColor,font:{size:9},maxTicksLimit:10},grid:{color:gridColor}},y:{ticks:{color:tickColor,font:{size:9},callback:function(v){return fmtBps(v)}},grid:{color:gridColor},beginAtZero:true}}}})
}
function renderMonitor(){
  var st=S.status;var hl=st&&st.health?st.health:{};var ok=hl.connected;var srv=st&&st.active_server;
  return h('div',null,
    h('div',{className:'card'},
      h('div',{className:'card-t'},t('monitor')),
      h('div',{className:'grid grid3',style:{marginBottom:'14px'}},
        h('div',{className:'stat'+(ok?' stat-green':' stat-red')},
          h('div',{className:'stat-l'},t('connected')),
          h('div',{className:'stat-v '+(ok?'on':'off')},ok?t('connected'):t('disconnected'))),
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('active')),
          h('div',{className:'stat-v'},srv?srv.name:'\u2014')),
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('latency')),
          h('div',{className:'stat-v'},hl.latency_ms?hl.latency_ms+'ms':'\u2014'))),
      h('div',{className:'grid grid3'},
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('external_ip')),
          h('div',{className:'stat-v',style:{fontSize:'14px'}},hl.external_ip?hl.external_ip:'\u2014')),
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('uptime')),
          h('div',{style:{marginTop:'4px'}},
            h('div',{style:{display:'flex',alignItems:'baseline',gap:'6px',marginBottom:'4px'}},
              h('span',{style:{fontSize:'10px',color:'var(--tx3)',minWidth:'70px'}},t('service_label')+':'),
              h('span',{style:{fontSize:'14px',fontWeight:700,fontFamily:'var(--m)'}},fmtUptime(st?st.uptime_seconds:0))),
            h('div',{style:{display:'flex',alignItems:'baseline',gap:'6px'}},
              h('span',{style:{fontSize:'10px',color:'var(--tx3)',minWidth:'70px'}},t('connection_label')+':'),
              h('span',{style:{fontSize:'14px',fontWeight:700,fontFamily:'var(--m)',color:hl.tt_uptime?'var(--gn)':'var(--tx3)'}},hl.tt_uptime?fmtUptime(hl.tt_uptime):'\u2014')))),
        h('div',{className:'stat'},
          h('div',{className:'stat-l'},t('hostname')),
          h('div',{className:'stat-v',style:{fontSize:'14px'}},srv?srv.hostname:'\u2014')))),
    h('div',{className:'card'},
      h('div',{className:'card-t'},
        h('span',null,t('network_traffic')),
        h('div',{className:'periods'},
          [{v:1,l:'1h'},{v:24,l:'24h'},{v:168,l:'7d'},{v:720,l:'30d'},{v:8760,l:'1y'}].map(function(p){
            return h('button',{className:'per'+(S.netPeriod===p.v?' on':''),onClick:function(){loadNetHistory(p.v).then(function(){R(drawNetChart)})}},p.l)}))),
      h('div',{className:'chart-wrap'},h('canvas',{id:'net-chart'}))),
    h('div',{className:'card'},
      h('div',{className:'card-t'},t('service_controls')),
      h('div',{className:'bg'},
        h('button',{className:'btn btn-sm',onClick:function(e){confirmSvcAct('restart',e.currentTarget)}},t('restart')),
        h('button',{className:'btn btn-sm btn-d',onClick:function(e){confirmSvcAct('stop',e.currentTarget)}},t('stop')),
        h('button',{className:'btn btn-sm btn-p',onClick:function(e){svcAct('start',e.currentTarget)}},t('start')))),
    renderFailoverLog());
}

function renderFailoverLog(){
  var log=S.failoverLog;var ps=10;var pages=Math.ceil(log.length/ps)||1;
  if(S.flPage>=pages)S.flPage=pages-1;if(S.flPage<0)S.flPage=0;
  var slice=log.slice(S.flPage*ps,S.flPage*ps+ps);
  return h('div',{className:'card'},
    h('div',{className:'card-t'},t('failover_log')),
    log.length===0?h('div',{style:{color:'var(--tx3)',fontSize:'12px',textAlign:'center',padding:'20px'}},t('no_failover_log')):
    h('div',null,
      h('div',{className:'tbl-wrap'},h('table',{className:'tbl'},
        h('thead',null,h('tr',null,
          h('th',null,t('event_time')),h('th',null,t('from_server')),h('th',null,t('to_server')),h('th',null,t('reason')))),
        h('tbody',null,slice.map(function(e){return h('tr',null,
          h('td',null,typeof e.ts==='string'?e.ts.replace('T',' '):new Date(e.ts*1000).toLocaleString()),
          h('td',null,srvName(e.from)),h('td',null,srvName(e.to)),h('td',null,failReason(e.reason)))})))),
      pages>1?h('div',{style:{display:'flex',justifyContent:'center',gap:'8px',marginTop:'10px'}},
        h('button',{className:'btn btn-xs',disabled:S.flPage===0,onClick:function(){S.flPage--;R()}},t('prev')),
        h('span',{style:{fontSize:'11px',color:'var(--tx3)',lineHeight:'26px'}},t('page')+' '+(S.flPage+1)+'/'+pages),
        h('button',{className:'btn btn-xs',disabled:S.flPage>=pages-1,onClick:function(){S.flPage++;R()}},t('next'))):null));
}
'''
