let state={page:1,pageSize:30,total:0,nPages:1,rows:[],selectedRun:null,selectedRuns:new Set(),plotData:null};
const $=id=>document.getElementById(id);

function fmt(v){if(!v)return '';try{return new Date(v).toLocaleString();}catch{return String(v)}}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]))}

async function fetchRuns(){
  const q=encodeURIComponent($('search').value||'');
  const st=encodeURIComponent($('statusFilter').value||'');
  const r=await fetch(`/api/v2/runs?page=${state.page}&page_size=${state.pageSize}&q=${q}&status=${st}`);
  const j=await r.json(); Object.assign(state,{total:j.total,nPages:j.n_pages,page:j.page,rows:j.rows});
  renderRuns();
}

function renderRuns(){
  const tb=$('runsTable').querySelector('tbody'); tb.innerHTML='';
  for(const row of state.rows){
    const tr=document.createElement('tr'); if(state.selectedRun===row.run_id)tr.classList.add('selected');
    tr.innerHTML=`<td><input type="checkbox" ${state.selectedRuns.has(row.run_id)?'checked':''}></td><td>${row.run_id}</td><td>${esc(row.mode)}</td><td class="${row.has_raw_records?'good':'bad'}">${row.has_raw_records?'yes':'no'}</td><td class="${row.has_event_info?'good':'warn'}">${row.has_event_info?'yes':'no'}</td><td>${esc(row.status)}</td><td>${fmt(row.start)}</td>`;
    tr.querySelector('input').addEventListener('click',e=>{e.stopPropagation(); if(e.target.checked)state.selectedRuns.add(row.run_id); else state.selectedRuns.delete(row.run_id)});
    tr.addEventListener('click',()=>{state.selectedRun=row.run_id; history.replaceState(null,'',`?run_id=${row.run_id}`); renderRuns(); loadRun(row.run_id)});
    tb.appendChild(tr);
  }
  $('pageInfo').textContent=`Page ${state.page}/${state.nPages} (${state.total} runs)`;
}

async function loadRun(runId){
  $('plotStatus').textContent='Loading run...';
  const [runRes,avRes,plRes]=await Promise.all([fetch(`/api/v2/run/${runId}`),fetch(`/api/v2/run/${runId}/availability`),fetch(`/api/v2/run/${runId}/plot-data?max_points=100000`)]);
  const run=await runRes.json(); const av=await avRes.json(); const pl=await plRes.json(); state.plotData=pl;
  const ps=run.processing_status||{};
  $('runSummary').textContent=`Run: ${run.run_id}\nMode: ${run.mode}\nStart: ${fmt(run.start)}\nEnd: ${fmt(run.end)}\nStatus: ${ps.status||'unknown'} @ ${fmt(ps.time)}\nTags: ${(run.tags||[]).map(t=>t.name).join(', ')||'-'}\nComments: ${(run.comments||[]).length}`;
  $('runJson').value=JSON.stringify(run.raw_doc||{},null,2);
  const ab=$('availTable').querySelector('tbody'); ab.innerHTML='';
  for(const r of av){
    const tr=document.createElement('tr');
    tr.innerHTML=`<td>${esc(r.type)}</td><td>${esc(r.lineage_hash)}</td><td>${esc(r.current_lineage_hash||'')}</td><td class="${r.loadable?'good':'warn'}">${r.loadable?'yes':'no'}</td><td>${r.n_files}</td><td>${r.size_mb}</td><td>${esc(r.reason)}</td>`;
    ab.appendChild(tr);
  }
  renderPlots();
}

function rebin2D(x,y,bx,by){
  if(!x.length||!y.length)return {z:[],x:[],y:[]};
  const xmin=Math.min(...x),xmax=Math.max(...x),ymin=Math.min(...y),ymax=Math.max(...y);
  const z=Array.from({length:by},()=>Array(bx).fill(0));
  for(let i=0;i<Math.min(x.length,y.length);i++){
    const xi=Math.min(bx-1,Math.max(0,Math.floor((x[i]-xmin)/(xmax-xmin+1e-12)*bx)));
    const yi=Math.min(by-1,Math.max(0,Math.floor((y[i]-ymin)/(ymax-ymin+1e-12)*by)));
    z[yi][xi]++;
  }
  const xv=Array.from({length:bx},(_,i)=>xmin+(i+0.5)*(xmax-xmin)/bx);
  const yv=Array.from({length:by},(_,i)=>ymin+(i+0.5)*(ymax-ymin)/by);
  return {z,x:xv,y:yv};
}

function renderPlots(){
  const d=state.plotData||{}; const bins=parseInt($('bins').value,10)||80; const log=$('logY').checked;
  $('plotStatus').textContent=d.reason||'';
  Plotly.newPlot('driftPlot',[{x:d.drift_time||[],type:'histogram',nbinsx:bins,marker:{color:'#4db6ff'}}],{title:'Drift Time',xaxis:{title:'drift time (ns)'},yaxis:{title:'counts'},paper_bgcolor:'#0f1729',plot_bgcolor:'#0f1729',font:{color:'#dce7ff'}});
  const s1=d.s1_area||[], s2=d.s2_area||[]; const h1=rebin2D(s1,s2,bins,bins);
  Plotly.newPlot('s1s2Plot',[{x:h1.x,y:h1.y,z:h1.z,type:'heatmap',colorscale:'Viridis',zsmooth:false,zmin:0,colorbar:{title:'counts'}}],{title:'S1 vs S2',xaxis:{title:'S1'},yaxis:{title:'S2'},paper_bgcolor:'#0f1729',plot_bgcolor:'#0f1729',font:{color:'#dce7ff'}});
  const x=d.x||[], y=d.y||[]; const h2=rebin2D(x,y,bins,bins);
  Plotly.newPlot('xyPlot',[{x:h2.x,y:h2.y,z:h2.z,type:'heatmap',colorscale:log?'Cividis':'Plasma',colorbar:{title:'counts'}}],{title:'XY Position',xaxis:{title:'x'},yaxis:{title:'y',scaleanchor:'x',scaleratio:1},paper_bgcolor:'#0f1729',plot_bgcolor:'#0f1729',font:{color:'#dce7ff'}});
}

async function submitSelected(){
  const run_ids=[...state.selectedRuns]; if(!run_ids.length){$('submitResult').textContent='Select runs first';return;}
  $('submitResult').textContent='Submitting...';
  const r=await fetch('/api/v2/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({run_ids,targets:['event_basics','event_positions','event_info']})});
  const j=await r.json();
  $('submitResult').textContent=`Submitted ${j.submitted}/${j.total}`;
  fetchRuns();
}

function init(){
  $('refreshBtn').onclick=()=>fetchRuns();
  $('search').oninput=()=>{state.page=1;fetchRuns()};
  $('statusFilter').onchange=()=>{state.page=1;fetchRuns()};
  $('prevPage').onclick=()=>{state.page=Math.max(1,state.page-1);fetchRuns()};
  $('nextPage').onclick=()=>{state.page=Math.min(state.nPages,state.page+1);fetchRuns()};
  $('submitSelected').onclick=submitSelected;
  $('bins').oninput=()=>renderPlots();
  $('logY').onchange=()=>renderPlots();
  const u=new URL(window.location.href); const rid=u.searchParams.get('run_id'); if(rid){state.selectedRun=parseInt(rid,10)}
  fetchRuns().then(()=>{if(state.selectedRun)loadRun(state.selectedRun)});
}

document.addEventListener('DOMContentLoaded',init);
