'use strict';
const $ = (id) => document.getElementById(id);
let token = '';
let scanTimer = null;
let cacheTimer = null;
let cacheSources = [];
let candidates = [];
let selected = new Set();
let currentPlan = null;
let chatHistory = [];
let busy = false;

const size = (value) => {
  if (typeof value !== 'number') return '—';
  let n = value;
  for (const u of ['B', 'KB', 'MB', 'GB', 'TB']) {
    if (n < 1024 || u === 'TB') return `${n.toFixed(1)} ${u}`;
    n /= 1024;
  }
};
const dom = (tag, className, text = '') => {
  const element = document.createElement(tag);
  if (className) element.className = className;
  element.textContent = text;
  return element;
};
function toast(text) {
  $('toast').textContent = text;
  $('toast').classList.add('show');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => $('toast').classList.remove('show'), 4500);
}
async function request(path, body = null) {
  const options = body === null ? {} : {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Local-Token': token}, body: JSON.stringify(body)};
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'تعذر تنفيذ الطلب');
  return result;
}
function showView(view) {
  document.querySelectorAll('.view').forEach(el => el.classList.toggle('active', el.id === `view-${view}`));
  document.querySelectorAll('.nav').forEach(el => el.classList.toggle('active', el.dataset.view === view));
  $('section-label').textContent = ({overview:'نظرة عامة',cleanup:'الكاش والتنظيف',activity:'سجل النشاط',settings:'الإعدادات'})[view];
  if (view === 'activity') loadActivity();
}
function displayScan(scan) {
  const result = scan?.result;
  const running = scan?.status === 'running';
  $('scan-button').disabled = running;
  $('scan-status').hidden = !running;
  $('scan-status-text').textContent = `جارِ فحص ${scan?.progress || 'مجلدات القرص'}...`;
  if (!result || !result.total) return;
  const percent = Math.min(100, Math.round(100 * result.used / result.total));
  $('total-disk').textContent = size(result.total);
  $('used-disk').textContent = size(result.used);
  $('free-disk').textContent = size(result.free);
  $('used-percent').textContent = `${percent}% من إجمالي القرص`;
  $('ring-percent').textContent = `${percent}%`;
  $('donut').style.background = `conic-gradient(#866de0 0% ${percent}%, #282d39 ${percent}% 100%)`;
  $('legend-used').textContent = size(result.used);
  $('legend-free').textContent = size(result.free);
  $('scan-time').textContent = 'آخر فحص مكتمل';
  $('scan-note').textContent = result.errors || result.skipped_links || result.truncated
    ? `تنبيه: تعذر قراءة ${result.errors} عناصر، وتم تجاوز ${result.skipped_links} رابط أو junction. قد تكون أحجام المجلدات غير مكتملة؛ حد الفحص: ${result.truncated ? "تم بلوغه" : "لم يُبلغ"}.`
    : 'الفحص تم بنجاح. تحليل الملفات قراءة فقط، ويمكن مراجعة فرص التنظيف من تبويب التنظيف الآمن.';
  const list = $('folder-list');
  list.replaceChildren();
  const max = Math.max(...result.folders.map(x => x.bytes), 1);
  result.folders.slice(0,8).forEach(folder => {
    const item = dom('div','folder-item');
    const line = dom('div','folder-line');
    line.append(dom('span','',folder.name), dom('b','',size(folder.bytes)));
    const track = dom('div','track');
    const fill = dom('div','fill');
    fill.style.width = `${Math.max(0.5,100 * folder.bytes/max)}%`;
    track.append(fill);item.append(line,track);list.append(item);
  });
  if (!result.folders.length) list.append(dom('p','empty','لم يتم العثور على مجلدات يمكن قراءتها.'));
  $('files-count').textContent = `${(result.files_seen || 0).toLocaleString('ar-SA')} ملف ممسوح${result.truncated?' · فحص جزئي':''}`;
  const big = $('largest-files');big.replaceChildren();
  (result.largest_files || []).slice(0,16).forEach(file => {
    const row=dom('div','data-row');row.append(dom('span','',file.path),dom('b','',size(file.bytes)));big.append(row);
  });
  if (!big.childElementCount)big.append(dom('p','empty','لم تُكتشف ملفات فوق 32 MB ضمن المناطق المقروءة.'));
  const types=$('file-types');types.replaceChildren();
  (result.file_types||[]).slice(0,12).forEach(item=>{
    const row=dom('div','data-row');row.append(dom('span','',item.extension),dom('b','',size(item.bytes)));types.append(row);
  });
  if (!types.childElementCount)types.append(dom('p','empty','لا توجد بيانات امتدادات.'));
}
async function checkScan() {
  try {
    const scan = await request('/api/scan');
    displayScan(scan);
    if (scan.status !== 'running' && scanTimer) {
      clearInterval(scanTimer); scanTimer = null;
      if (scan.status === 'error') toast(`تعذر الفحص: ${scan.progress}`);
      if (scan.status === 'complete') toast('اكتمل فحص القرص بدون تعديل أي ملف.');
    }
  } catch(err) { toast(err.message); clearInterval(scanTimer); scanTimer = null; }
}
async function startScan() {
  try {
    const outcomes=await Promise.allSettled([request('/api/scan/start',{}),request('/api/caches/start',{})]);
    if(outcomes.every(r=>r.status==='rejected'))throw outcomes[0].reason;
    if(outcomes[1].status==='fulfilled')ensureCachePolling();
    if(outcomes[0].status==='rejected')toast('فحص القرص جارٍ بالفعل؛ بدأنا فحص الكاش');
    displayScan({status:'running',progress:'Starting'});
    if (scanTimer) clearInterval(scanTimer);
    scanTimer = setInterval(checkScan, 1400);
  } catch(err) {toast(err.message);}
}
function ensureCachePolling(){
  if(!cacheTimer)cacheTimer=setInterval(checkCache,1500);
  checkCache();
}
function showSourceCards(report){
  cacheSources=report.sources||[];
  const root=$('cache-sources');root.replaceChildren();
  $('cache-audit-meta').textContent = `${cacheSources.length} مصدر · تم قياس ${size(report.inspected_bytes||0)} · ${report.limited?'نتائج جزئية': 'قياس مكتمل ضمن المواقع المعروفة'} · ${report.errors||0} أخطاء`;
  cacheSources.forEach(src=>{
    const card=dom('article','source-card');
    card.append(dom('h3','',src.label),dom('div','source-size',size(src.bytes)));
    const badge=dom('div',`risk ${src.cleanable?'':'protected'}`,src.cleanable?`مراجعة ${src.risk}`:'للقراءة فقط · محمي');
    card.append(badge,dom('small','',src.cleanable?`مؤهل للاختيار: ${size(src.eligible_bytes)}`:'غير مسموح بالحذف من التطبيق'));
    card.append(dom('p','source-path',src.path),dom('p','',src.note));
    if(src.limited)card.append(dom('p','','⚠ هذه النتيجة جزئية بسبب الحد أو الملفات غير المتاحة'));
    root.append(card);
  });
  if(!root.childElementCount)root.append(dom('p','empty','لم يُعثر على مصادر كاش معروفة.'));
}
async function checkCache(){
  try{
    const state=await request('/api/caches');
    const running=state.status==='running';
    $('cache-status').hidden=!running;
    $('cache-status-text').textContent=`فحص الكاش: ${state.progress||'جارِ التحليل'}`;
    $('candidates-button').disabled=running;
    if(state.status==='complete' && state.result){
      showSourceCards(state.result);
      showCandidates(state.result);
      if(cacheTimer){clearInterval(cacheTimer);cacheTimer=null;toast('اكتمل تحليل الكاش ومصادر الملفات.');}
    } else if(state.status==='error'){
      if(cacheTimer){clearInterval(cacheTimer);cacheTimer=null;}
      toast(`تعذر فحص الكاش: ${state.progress}`);
    } else if(state.status==='idle' && cacheTimer){clearInterval(cacheTimer);cacheTimer=null;}
  }catch(err){if(cacheTimer){clearInterval(cacheTimer);cacheTimer=null;}toast(err.message);}
}
function visibleCandidates(){
  const source=$('source-filter').value;
  return candidates.filter(item=>!source || item.category===source);
}
function updateSelection() {
  const items = candidates.filter(item => selected.has(item.id));
  $('selection-count').textContent = `${items.length} محدد`;
  $('selected-size').textContent = size(items.reduce((sum,x)=>sum + x.bytes,0));
  $('plan-button').disabled = !items.length;
  $('select-all').textContent = 'تحديد الظاهر';
}
function renderCandidates(){
  const list=$('candidates-list');list.replaceChildren();
  const visible=visibleCandidates();
  if(!visible.length){
    const tr=dom('tr');const td=dom('td','empty','ما فيه ملفات مؤهلة في التصنيف المحدد.');td.colSpan=5;tr.append(td);list.append(tr);
  }
  visible.slice(0,200).forEach(item=>{
    const tr=dom('tr');const pick=dom('td');const box=dom('input');box.type='checkbox';box.checked=selected.has(item.id);
    box.setAttribute('aria-label',`تحديد ${item.path}`);
    box.addEventListener('change',()=>{box.checked?selected.add(item.id):selected.delete(item.id);updateSelection();});pick.append(box);
    const src=cacheSources.find(s=>s.key===item.category);
    tr.append(pick,dom('td','path',item.path),dom('td','tag-risk',`${src?.label||item.category} · ${item.risk}`),dom('td','',`${item.age_days} يوم`),dom('td','',size(item.bytes)));
    list.append(tr);
  });
  if(visible.length>200){const tr=dom('tr');const td=dom('td','empty',`نعرض أول 200 من ${visible.length} ملف. استخدم فلتر المصدر لعرض ملفات أخرى.`);td.colSpan=5;tr.append(td);list.append(tr);}
  updateSelection();
}
function showCandidates(data){
  candidates=data.items||[];
  selected.clear();
  $('cleanup-space').textContent=data.available?size(data.total_bytes):'—';
  $('candidate-meta').textContent=data.available?`${candidates.length} ملف مؤهل للموافقة · ${size(data.total_bytes)} · ${data.limited?'النتائج جزئية':'الانتهاء من المواقع المعروفة'}`:(data.reason||'لم يتم العثور على ملفات مؤهلة');
  const filter=$('source-filter'),previous=filter.value;
  filter.replaceChildren();const all=dom('option','','كل المصادر');all.value='';filter.append(all);
  cacheSources.filter(s=>s.eligible_count).forEach(s=>{const option=dom('option','',s.label);option.value=s.key;filter.append(option);});
  filter.value=[...filter.options].some(x=>x.value===previous)?previous:'';
  renderCandidates();
}
async function refreshCandidates(){
  try {await request('/api/caches/start',{});ensureCachePolling();toast('بدأ فحص الكاش والملفات الحقيقية.');}
  catch(err){toast(err.message);}
}
function closeModal() {$('confirm-modal').hidden=true;currentPlan=null;$('confirm-input').value='';$('execute-delete').disabled=true;}
async function planCleanup() {
  try {
    currentPlan=await request('/api/plan',{ids:[...selected]});
    $('modal-summary').textContent=`${currentPlan.items.length} ملف · ${size(currentPlan.total_bytes)} · صلاحية الخطة 10 دقائق`;
    const list=$('modal-items');list.replaceChildren();
    currentPlan.items.slice(0,25).forEach(item=>list.append(dom('div','',`${item.path} · ${size(item.bytes)}`)));
    if(currentPlan.items.length>25)list.append(dom('div','',`... و${currentPlan.items.length-25} ملف إضافي`));
    $('confirm-modal').hidden=false;
    $('confirm-input').focus();
  }catch(err){toast(err.message);}
}
async function executePlan(dryRun) {
  if(!currentPlan)return;
  $('execute-delete').disabled = true;
  $('dry-run').disabled = true;
  try {
    const result=await request('/api/execute',{plan_id:currentPlan.plan_id,confirm:$('confirm-input').value,dry_run:dryRun});
    const deleted=result.results.filter(r=>r.status==='deleted').length;
    const simulated=result.results.filter(r=>r.status==='dry_run').length;
    const other=result.results.length-deleted-simulated;
    closeModal();
    toast(dryRun?`المحاكاة: ${simulated} ملف مؤهل. لم يُحذف شيء.`:`حُذف ${deleted} ملف · المساحة المقدّرة ${size(result.freed_estimate)} · تم تجاوز ${other}`);
    if(!dryRun)await refreshCandidates();
  }catch(err){toast(err.message);}
  finally{$('dry-run').disabled=false;}
}
async function loadActivity(){
  try{
    const r=await request('/api/activity');const list=$('activity-list');list.replaceChildren();
    if(!r.entries.length)return list.append(dom('p','empty','لا توجد عمليات مسجلة بعد.'));
    r.entries.forEach(entry=>{
      const row=dom('div','activity-row');row.append(dom('div','activity-icon',entry.event==='scan'?'◫':'✧'));
      const body=dom('div');body.append(dom('b','',entry.event==='scan'?'فحص القرص':entry.event==='cache_audit'?'فحص الكاش':'تنظيف ملفات محددة'));
      body.append(dom('p','',entry.event==='scan'?`ملفات ممسوحة: ${entry.files_seen||0} · تحذيرات: ${entry.warnings||0}`:entry.event==='cache_audit'?`مصادر: ${entry.sources||0} · مؤهل للمراجعة: ${size(entry.eligible_bytes||0)}`:`تم الحذف: ${entry.deleted||0} · وفّر تقريبًا: ${size(entry.freed_estimate||0)} · غير مكتمل: ${entry.failed||0}`));
      body.append(dom('p','small-muted',new Date(entry.at).toLocaleString('ar-SA')));
      row.append(body);list.append(row);
    });
  }catch(err){toast(err.message);}
}
function addMessage(text,role){
  const row=dom('div',`chat-message ${role}`);
  if(role==='assistant')row.append(dom('span','avatar','✧'));
  row.append(dom('div','bubble',text));
  $('chat-thread').append(row);$('chat-thread').scrollTop=$('chat-thread').scrollHeight;
}
async function sendChat(message){
  if(busy||!message.trim())return;
  busy=true;$('send-button').disabled=true;
  addMessage(message,'user');$('chat-input').value='';
  const history=chatHistory.slice(-12);
  try{
    const response=await request('/api/chat',{message,history});
    addMessage(response.text,'assistant');
    if(response.action==='scan_started'){
      ensureCachePolling();
      const status=await request('/api/scan');
      if(status.status==='running'&&!scanTimer)scanTimer=setInterval(checkScan,1500);
    }
    chatHistory.push({role:'user',content:message},{role:'assistant',content:response.text});
    chatHistory=chatHistory.slice(-12);
  }catch(err){addMessage(`تعذر الاتصال: ${err.message}`,'assistant');}
  finally{busy=false;$('send-button').disabled=false;}
}
function modelsList(models,current){
  const select=$('model-select');select.replaceChildren();
  if(!models.length){const option=dom('option','','ما فيه موديلات مثبتة');option.value='';select.append(option);return;}
  models.forEach(m=>{const option=dom('option','',m);option.value=m;select.append(option);});
  select.value=models.includes(current)?current:models[0];
}
async function initialize(){
  document.querySelectorAll('.nav').forEach(btn=>btn.addEventListener('click',()=>showView(btn.dataset.view)));
  $('scan-button').addEventListener('click',startScan);
  $('cancel-scan').addEventListener('click',async()=>{await request('/api/scan/cancel',{});toast('تم إرسال طلب إيقاف الفحص');});
  $('refresh-button').addEventListener('click',()=>{checkScan();loadActivity();});
  $('candidates-button').addEventListener('click',refreshCandidates);
  $('source-filter').addEventListener('change',renderCandidates);
  $('select-all').addEventListener('click',()=>{
    const visible=visibleCandidates().slice(0,200);
    const all=visible.every(item=>selected.has(item.id));
    visible.forEach(item=>all?selected.delete(item.id):selected.add(item.id));
    renderCandidates();
  });
  $('plan-button').addEventListener('click',planCleanup);
  $('modal-close').addEventListener('click',closeModal);
  $('confirm-modal').addEventListener('click',event=>{if(event.target===$('confirm-modal'))closeModal();});
  $('confirm-input').addEventListener('input',()=>{$('execute-delete').disabled=$('confirm-input').value!=='DELETE SELECTED FILES';});
  $('execute-delete').addEventListener('click',()=>executePlan(false));
  $('dry-run').addEventListener('click',()=>executePlan(true));
  $('activity-button').addEventListener('click',loadActivity);
  $('chat-form').addEventListener('submit',event=>{event.preventDefault();sendChat($('chat-input').value);});
  $('chat-input').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChat($('chat-input').value);}});
  document.querySelectorAll('.prompt-chip').forEach(btn=>btn.addEventListener('click',()=>sendChat(btn.dataset.prompt)));
  $('save-model').addEventListener('click',async()=>{
    try {const r=await request('/api/model',{model:$('model-select').value});toast(`تم اختيار ${r.model}`);}catch(err){toast(err.message);}
  });
  try {
    const status=await request('/api/status');token=status.csrf;
    $('ollama-state').textContent=status.models.length?`● Ollama · ${status.models.length} models`:'○ Ollama غير متصل';
    modelsList(status.models,status.model);
    displayScan(status.scan);
    if(status.scan.status==='running')scanTimer=setInterval(checkScan,1400);
    const old=await request('/api/candidates');
    if(old.available){showSourceCards(old);showCandidates(old);}
    if(status.cache?.status==='running')ensureCachePolling();
    else if(status.cache?.status==='complete' && status.cache.result){showSourceCards(status.cache.result);showCandidates(status.cache.result);}
  }catch(err){toast(`تعذر بدء التطبيق: ${err.message}`);}
}
initialize();