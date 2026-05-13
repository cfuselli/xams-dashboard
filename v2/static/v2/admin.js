const $ = (id) => document.getElementById(id);

function renderBackfillPreview(j){
  const p=(j.preview||[]).slice(0,40);
  const lines=p.map(r=>{
    const b=r.before||{}, a=r.after||{};
    const from=`${b.science_run_id||'-'}|${b.run_class||'-'}|${b.source_type||'-'}`;
    const to=`${a.science_run_id||'-'}|${a.run_class||'-'}|${a.source_type||'-'}`;
    return `${r.run_id} ${r.changed?'CHANGE':'KEEP'} ${from} -> ${to}`;
  });
  $('backfillPreviewText').textContent=lines.length?lines.join('\n'):'No matching runs.';
}

function buildPayload(dryRun){
  return {
    science_run_id: ($('backfillSr').value || '').trim(),
    run_class: ($('backfillRunClass').value || '').trim(),
    source_type: ($('backfillSourceType').value || '').trim(),
    run_id_min: ($('backfillRunMin').value || '').trim(),
    run_id_max: ($('backfillRunMax').value || '').trim(),
    only_missing: $('backfillOnlyMissing').checked,
    dry_run: dryRun
  };
}

async function runBackfill(dryRun){
  const payload=buildPayload(dryRun);
  if(!dryRun && !payload.science_run_id){
    $('backfillResult').textContent='Apply blocked: set Science Run first.';
    return;
  }
  if(!dryRun && !window.confirm('Apply bookkeeping backfill to matched runs?')) return;
  $('backfillResult').textContent=dryRun?'Previewing...':'Applying...';
  const r=await fetch('/api/v2/backfill-bookkeeping',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const j=await r.json();
  $('backfillResult').textContent=`matched ${j.matched}, updates ${j.candidate_updates}, applied ${j.applied}, only_missing=${j.only_missing}`;
  renderBackfillPreview(j);
}

async function refreshQueue(){
  try{
    const rq=await fetch('/api/v2/jobs');
    const jq=await rq.json();
    const c=jq.counts||{};
    $('heldJobs').textContent=`held ${c.held||0}, running ${c.running||0}, idle ${c.idle||0}`;
    const rows=(jq.rows||[]).slice(0,15);
    $('jobsList').textContent=rows.map(r=>`${r.cluster_id}.${r.proc_id} ${r.status} ${r.batch_name||''}`).join('\n');
  }catch(_e){
    $('jobsList').textContent='Failed to load queue status';
  }
}

async function init(){
  const m=await fetch('/api/v2/meta').then(r=>r.json()).catch(()=>({}));
  if(m.active_science_run){
    $('backfillSr').value=m.active_science_run;
  }
  $('backfillPreview').onclick=()=>runBackfill(true);
  $('backfillApply').onclick=()=>runBackfill(false);
  refreshQueue();
  setInterval(refreshQueue, 20000);
}

document.addEventListener('DOMContentLoaded', init);
