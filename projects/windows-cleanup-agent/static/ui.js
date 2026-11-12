'use strict';
const $ = (id) => document.getElementById(id);
let token = '';
let scanTimer = null;
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
  $('section-label').textContent = ({overview:'نظرة عامة',cleanup:'التنظيف الآمن',activity:'سجل النشاط',settings:'الإعدادات'})[view];
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
  $('scan-note').textContent = result.errors || result.skipped_links
    ? `تنبيه: تعذر قراءة ${result.errors} عناصر، وتم تجاوز ${result.skipped_links} رابط أو junction. قد تكون أحجام المجلدات غير مكتملة.`
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
    await request('/api/scan/start',{});
    displayScan({status:'running',progress:'Starting'});
    if (scanTimer) clearInterval(scanTimer);
    scanTimer = setInterval(checkScan, 1400);
  } catch(err) {toast(err.message);}
}
function updateSelection() {
  const items = candidates.filter(item => selected.has(item.id));
  $('selection-count').textContent = `${items.length} محدد`;
  $('selected-size').textContent = size(items.reduce((sum,x)=>sum + x.bytes,0));
  $('plan-button').disabled = !items.length;
  $('select-all').textContent = selected.size === candidates.length && candidates.length ? 'إلغاء التحديد' : 'تحديد الكل';
}
function showCandidates(data) {
  candidates = data.items || [];
  selected.clear();
  $('cleanup-space').textContent = data.available ? size(data.total_bytes) : '—';
  $('candidate-meta').textContent = data.available ? `${candidates.length} ملف مؤهل · ${size(data.total_bytes)} · ${data.limited ? 'نتائج محدودة لتخفيف الحمل' : 'اكتمل البحث'}` : (data.reason || 'لم يتم العثور على ملفات مؤهلة');
  const list = $('candidates-list');list.replaceChildren();
  if (!candidates.length) {
    const tr = dom('tr');const td=dom('td','empty',data.available?'ما لقينا ملفات Temp مؤهلة للحذف حاليًا.':'لا يمكن الوصول إلى مجلد Temp في هذا الجهاز.');
    td.colSpan=4;tr.append(td);list.append(tr);
  }
  candidates.forEach(item => {
    const tr=dom('tr');const pick=dom('td');const box=dom('input');box.type='checkbox';box.setAttribute('aria-label',`تحديد ${item.path}`);
    box.addEventListener('change',()=>{box.checked?selected.add(item.id):selected.delete(item.id);updateSelection();});
    pick.append(box);
    tr.append(pick,dom('td','path',item.path),dom('td','',`${item.age_days} يوم`),dom('td','',size(item.bytes)));
    tr.dataset.id = item.id;
    list.append(tr);
  });updateSelection();
}
async function refreshCandidates() {
  $('candidates-button').disabled = true;
  try {showCandidates(await request('/api/candidates/refresh',{})); toast('تم تحليل ملفات Temp المحلية فقط.');}
  catch(err){toast(err.message);}
  finally{$('candidates-button').disabled=false;}
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
      const body=dom('div');body.append(dom('b','',entry.event==='scan'?'فحص القرص':'تنظيف ملفات مؤقتة'));
      body.append(dom('p','',entry.event==='scan'?`تحذيرات الفحص: ${entry.warnings || 0}`:`تم الحذف: ${entry.deleted || 0} · المساحة المقدّرة: ${size(entry.freed_estimate || 0)} · غير مكتمل: ${entry.failed || 0}`));
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
  $('select-all').addEventListener('click',()=>{
    const all=selected.size===candidates.length;selected=new Set(all?[]:candidates.map(x=>x.id));
    document.querySelectorAll('#candidates-list input[type=checkbox]').forEach(box=>{box.checked=!all;});updateSelection();
  });
  $('plan-button').addEventListener('click',planCleanup);
  $('modal-close').addEventListener('click',closeModal);
  $('confirm-modal').addEventListener('click',event=>{if(event.target===$('confirm-modal'))closeModal();});
  $('confirm-input').addEventListener('input',()=>{$('execute-delete').disabled=$('confirm-input').value!=='DELETE TEMP FILES';});
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
    showCandidates(await request('/api/candidates'));
  }catch(err){toast(`تعذر بدء التطبيق: ${err.message}`);}
}
initialize();