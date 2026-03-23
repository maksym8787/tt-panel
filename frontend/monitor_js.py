MONITOR_JS = r'''
var charts={};
var chartColors={
  sessions:{border:'#3b9eff',bg:'rgba(59,158,255,0.08)'},
  download:{border:'#22c55e',bg:'rgba(34,197,94,0.08)'},
  upload:{border:'#f59e0b',bg:'rgba(245,158,11,0.08)'},
  memory:{border:'#a78bfa',bg:'rgba(167,139,250,0.08)'},
  cpu:{border:'#06b6d4',bg:'rgba(6,182,212,0.08)'}
};
function isDarkMode(){return getComputedStyle(document.documentElement).getPropertyValue('--bg').trim().startsWith('#0')}
var chartTheme=function(){var dk=isDarkMode();return{grid:dk?'rgba(255,255,255,.06)':'rgba(0,0,0,.08)',tick:dk?'rgba(255,255,255,.5)':'rgba(0,0,0,.5)',legend:dk?'#c8d0da':'#374151',tipBg:dk?'#131a24':'#ffffff',tipBorder:dk?'#1e2a3a':'#d0d5dd',tipTitle:dk?'#e2e8f0':'#1a1a2e',tipBody:dk?'#8899aa':'#4a5568'}};
var chartOpts=function(yCallback){var ct=chartTheme();return{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,labels:{color:ct.legend,font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:ct.tipBg,borderColor:ct.tipBorder,borderWidth:1,titleColor:ct.tipTitle,bodyColor:ct.tipBody,titleFont:{family:'DM Sans',size:12,weight:600},bodyFont:{family:'JetBrains Mono',size:11},padding:10,cornerRadius:8,displayColors:true,boxWidth:8,boxHeight:8,boxPadding:4}},scales:{x:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:8,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},callback:yCallback||undefined,maxTicksLimit:5},grid:{color:ct.grid,drawBorder:false},border:{display:false}}}}};
var mkDataset=function(label,data,color,fill){return{label:label,data:data,borderColor:color.border,backgroundColor:color.bg,fill:fill!==false,tension:.35,pointRadius:0,pointHoverRadius:4,borderWidth:1.5}};

function updateChart(key,canvas,cfg){
  if(!canvas)return;
  // Check if old chart still points to a valid (attached) canvas
  if(charts[key]){
    if(charts[key].canvas&&charts[key].canvas.isConnected){
      // Canvas still in DOM — update in place (no flicker)
      var ch=charts[key];
      ch.data.labels=cfg.data.labels;
      for(var i=0;i<cfg.data.datasets.length;i++){
        if(ch.data.datasets[i]){ch.data.datasets[i].data=cfg.data.datasets[i].data}
        else{ch.data.datasets.push(cfg.data.datasets[i])}
      }
      while(ch.data.datasets.length>cfg.data.datasets.length)ch.data.datasets.pop();
      ch.update('none');
      return;
    }
    // Canvas was removed from DOM — destroy old instance
    try{charts[key].destroy()}catch(x){}
  }
  charts[key]=new Chart(canvas,cfg);
}

function drawAllCharts(){
  if(!window.Chart){setTimeout(drawAllCharts,500);return}
  if(!S.history||!S.history.snapshots.length)return;
  var d=S.history.snapshots;
  var labels=d.map(function(x){return ts2t(x.ts)});

  var c1=document.getElementById('ch-sessions');
  if(c1){updateChart('sess',c1,{type:'line',data:{labels:labels,datasets:[mkDataset(t('active_sessions'),d.map(function(x){return x.sessions}),chartColors.sessions)]},options:chartOpts()})}


  var c3=document.getElementById('ch-resources');
  if(c3){
    var ct=chartTheme();
    var cpuPct=d.map(function(x,i){if(i===0)return 0;var dt=x.ts-d[i-1].ts;if(dt<=0)return 0;return Math.min(100,((x.cpu-d[i-1].cpu)/dt)*100)});
    updateChart('res',c3,{type:'line',data:{labels:labels,datasets:[
      {label:t('mem_cpu').split('/')[0].trim()+' MB',data:d.map(function(x){return x.mem/1048576}),borderColor:chartColors.memory.border,backgroundColor:chartColors.memory.bg,fill:true,tension:.35,pointRadius:0,borderWidth:1.5,yAxisID:'y'},
      {label:'CPU %',data:cpuPct,borderColor:chartColors.cpu.border,backgroundColor:'transparent',fill:false,tension:.35,pointRadius:0,borderWidth:1.5,yAxisID:'y1'}
    ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,labels:{color:ct.legend,font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:ct.tipBg,borderColor:ct.tipBorder,borderWidth:1,titleColor:ct.tipTitle,bodyColor:ct.tipBody,padding:10,cornerRadius:8}},scales:{x:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:8,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,position:'left',title:{display:true,text:t('mem_cpu').split('/')[0].trim()+' MB',color:ct.tick,font:{size:9}},ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{color:ct.grid},border:{display:false}},y1:{display:true,position:'right',title:{display:true,text:'CPU %',color:ct.tick,font:{size:9}},ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{display:false},border:{display:false},min:0}}}})}
}

function fmtMbps(v){if(v>=1000)return (v/1000).toFixed(1)+' Gbps';if(v>=1)return v.toFixed(1)+' Mbps';if(v>=0.001)return (v*1000).toFixed(0)+' Kbps';return '0'}
function drawTrafficChart(){
  if(!window.Chart){setTimeout(drawTrafficChart,500);return}
  if(!S.traffic||!S.traffic.hourly.length)return;
  var d=S.traffic.hourly;var c=document.getElementById('ch-traffic');
  var interval=3600;
  if(d.length>=2){var dt=d[1].ts-d[0].ts;if(dt>0)interval=dt}
  if(c){
    var ct=chartTheme();
    var labels=d.map(function(x){return ts2t(x.ts)});
    updateChart('traffic',c,{type:'line',data:{labels:labels,datasets:[
      {label:'\u2193 '+t('download'),data:d.map(function(x){return (x.out||0)*8/interval/1000000}),borderColor:'#22c55e',backgroundColor:'rgba(34,197,94,0.1)',borderWidth:2,fill:true,tension:.35,pointRadius:0,pointHoverRadius:4,pointHoverBackgroundColor:'#22c55e'},
      {label:'\u2191 '+t('upload'),data:d.map(function(x){return (x['in']||0)*8/interval/1000000}),borderColor:'#f59e0b',backgroundColor:'rgba(245,158,11,0.08)',borderWidth:2,fill:true,tension:.35,pointRadius:0,pointHoverRadius:4,pointHoverBackgroundColor:'#f59e0b'}
    ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,labels:{color:ct.legend,font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:ct.tipBg,borderColor:ct.tipBorder,borderWidth:1,titleColor:ct.tipTitle,bodyColor:ct.tipBody,padding:10,cornerRadius:8,callbacks:{label:function(ctx){return ctx.dataset.label+': '+fmtMbps(ctx.raw)}}}},scales:{x:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:8},maxTicksLimit:24,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},callback:function(v){return fmtMbps(v)},maxTicksLimit:5},grid:{color:ct.grid},border:{display:false}}}}})
  }
}

function drawConnChart(){
  if(!window.Chart)return;
  if(!S.connTimeline||!S.connTimeline.timeline.length)return;
  var d=S.connTimeline.timeline;var c=document.getElementById('ch-conns');
  if(c){
    var ct=chartTheme();
    var connColor={border:'#a78bfa',bg:'rgba(167,139,250,0.3)'};
    var ipColor={border:'#06b6d4',bg:'rgba(6,182,212,0.3)'};
    updateChart('conns',c,{type:'bar',data:{
      labels:d.map(function(x){return ts2t(x.ts)}),
      datasets:[
        {label:t('connections'),data:d.map(function(x){return x.connections}),backgroundColor:connColor.bg,borderColor:connColor.border,borderWidth:1,borderRadius:3,order:2},
        {label:t('unique_ips_label'),data:d.map(function(x){return x.unique_ips}),type:'line',borderColor:ipColor.border,backgroundColor:'transparent',borderWidth:2,tension:.35,pointRadius:2,pointBackgroundColor:ipColor.border,order:1,yAxisID:'y1'}
      ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:true,labels:{color:ct.legend,font:{family:'DM Sans',size:10},boxWidth:8,boxHeight:8,padding:12,usePointStyle:true}},tooltip:{backgroundColor:ct.tipBg,borderColor:ct.tipBorder,borderWidth:1,titleColor:ct.tipTitle,bodyColor:ct.tipBody,padding:10,cornerRadius:8}},scales:{x:{display:true,ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:8,maxRotation:0},grid:{display:false},border:{display:false}},y:{display:true,position:'left',title:{display:true,text:t('connections'),color:ct.tick,font:{size:9}},ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{color:ct.grid},border:{display:false}},y1:{display:true,position:'right',title:{display:true,text:t('unique_ips_label'),color:ct.tick,font:{size:9}},ticks:{color:ct.tick,font:{family:'JetBrains Mono',size:9},maxTicksLimit:5},grid:{display:false},border:{display:false},min:0}}}})
  }
}

function renderMonitor(){
  var periods=[{v:1,l:'1h'},{v:6,l:'6h'},{v:24,l:'24h'},{v:168,l:'7d'}];

  if(S.monLoading&&!S.history){return h('div',{className:'tab-content'},h('div',{className:'skeleton skel-chart'}),h('div',{className:'skeleton skel-chart'}),h('div',{className:'skeleton skel-chart'}))}

  return h('div',{className:'tab-content'},
    h('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'14px'}},
      h('div',{style:{fontSize:'12px',fontWeight:'600',color:'var(--tx2)'}},t('monitoring')),
      periodSelector(S.monPeriod,periods,function(v){loadHistory(v)})),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('active_sessions')),
      h('div',{className:'chart-wrap'},h('canvas',{id:'ch-sessions'}))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('network_traffic')),
      h('div',{className:'chart-wrap'},h('canvas',{id:'ch-traffic'}))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('cpu_memory')),
      h('div',{className:'chart-wrap'},h('canvas',{id:'ch-resources'}))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},h('span',null,t('user_connections'))),
      h('div',{className:'chart-wrap'},h('canvas',{id:'ch-conns'}))),

    h('div',{className:'card'},
      h('div',{className:'card-t'},t('online_users')),
      S.online&&S.online.online_users&&S.online.online_users.length?
        h('div',{style:{maxHeight:'200px',overflow:'auto'}},
          h('table',{className:'tbl'},
            h('thead',null,h('tr',null,h('th',null,''),h('th',null,t('ip_address')),h('th',null,t('location')),h('th',null,t('isp')),h('th',null,t('last_seen')))),
            h('tbody',null,S.online.online_users.map(function(u){var g=u.geo||{};return h('tr',null,
                h('td',null,h('span',{className:'dot dot-on'})),
                h('td',{style:{color:'var(--tx)',fontFamily:'var(--m)',fontSize:'11px'}},u.ip||'\u2014'),
                h('td',null,g.flag?(g.flag+' '):'',g.city?(g.city+', '):'',(g.country||'')),
                h('td',{style:{fontSize:'10px',color:'var(--tx2)'}},g.isp||'\u2014'),
                h('td',null,ago(u.last_seen)))})))):
        h('div',{style:{color:'var(--tx3)',fontSize:'12px',padding:'12px 0',textAlign:'center'}},
          S.online&&S.online.live_sessions>0?t('sessions_active_no_ip'):t('no_active_conn')),
      S.online&&S.online.recently_active&&S.online.recently_active.length?h('div',{style:{marginTop:'12px',borderTop:'1px solid var(--bd)',paddingTop:'12px'}},
        h('div',{style:{fontSize:'10px',fontWeight:'600',color:'var(--tx3)',textTransform:'uppercase',letterSpacing:'.05em',marginBottom:'8px'}},t('recently_active')),
        h('div',{style:{display:'flex',flexWrap:'wrap',gap:'6px'}},S.online.recently_active.slice(0,20).map(function(u){var g=u.geo||{};return h('span',{className:'badge b-bl',style:{fontSize:'11px'}},(g.flag?g.flag+' ':'')+u.ip)}))):null),

    expandableCard('conn_log',
      h('span',{style:{display:'flex',alignItems:'center',justifyContent:'space-between',width:'100%'}},
        h('span',null,t('connection_log')),
        periodSelector(S.connPeriod,[{v:1,l:'1h'},{v:6,l:'6h'},{v:24,l:'24h'},{v:168,l:'7d'}],function(v){loadConns(v)})),
      S.conns&&S.conns.connections&&S.conns.connections.length?h('div',null,
        h('table',{className:'tbl',style:{tableLayout:'fixed',width:'100%'}},
          h('thead',null,h('tr',null,h('th',{style:{width:'14%'}},t('time')),h('th',{style:{width:'18%'}},t('ip')),h('th',{style:{width:'22%'}},t('user_agent')),h('th',{style:{width:'32%'}},t('destination')),h('th',{style:{width:'14%'}},t('event')))),
          h('tbody',null,paginatedList('connlog',S.conns.connections,function(c){return h('tr',null,
              h('td',null,ts2dt(c.ts)),
              h('td',{style:{color:c.ip?'var(--tx)':'',overflow:'hidden',textOverflow:'ellipsis'}},c.ip||''),
              h('td',{style:{overflow:'hidden',textOverflow:'ellipsis'}},c.ua||''),
              h('td',{style:{overflow:'hidden',textOverflow:'ellipsis'}},c.dst||''),
              h('td',null,h('span',{className:'badge '+(c.event==='connect'?'b-gn':c.event==='disconnect'?'b-rd':'b-bl')},c.event||'')))},25)))):
        h('div',{style:{color:'var(--tx3)',fontSize:'12px',textAlign:'center',padding:'16px'}},t('no_conn_data'))),

    S.conns&&S.conns.top_destinations&&S.conns.top_destinations.length?
      expandableCard('top_dst',t('top_destinations'),
        h('table',{className:'tbl'},
          h('thead',null,h('tr',null,h('th',null,t('domain')),h('th',{style:{textAlign:'right'}},t('connections')))),
          h('tbody',null,S.conns.top_destinations.map(function(d){return h('tr',null,h('td',null,d.dst),h('td',{style:{textAlign:'right'}},String(d.count)))})))):null,

    h('div',{style:{display:'flex',justifyContent:'space-between',fontSize:'10px',color:'var(--tx3)',fontFamily:'var(--m)',marginTop:'8px',padding:'0 4px'}},
      S.conns&&S.conns.unique_ips?h('span',null,t('unique_ips')+': '+S.conns.unique_ips.length):null,
      S.dbSize?h('span',null,'DB: '+S.dbSize.db_mb+' MB | Log: '+S.dbSize.log_mb+' MB'):null)
  );
}

'''
