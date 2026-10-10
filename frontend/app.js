const API = '/api';
let allProducts = [];
let activeCategory = 'all';
let activeProduct = null;
let voiceEnabled = true;
let busy = false;
const $ = (id) => document.getElementById(id);
const fabricColors = {'Cloud white':'#e9e6db','Midnight black':'#30323a','Sage green':'#7f9a7b','Navy blue':'#334c78','Warm beige':'#d5b895','Sky blue':'#8ab8d9'};

async function api(path, options={}) {
  const response = await fetch(`${API}${path}`, {headers:{'Content-Type':'application/json'}, ...options});
  if (!response.ok) {
    let message = 'Something went wrong. Please try again.';
    try { const data = await response.json(); message = data.detail || message; } catch (_) {}
    throw new Error(message);
  }
  return response.json();
}
function escapeHtml(value='') { return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function formatPrice(value) { return `₹${Number(value).toLocaleString('en-IN',{maximumFractionDigits:0})}`; }
function productCard(p) {
  const color = fabricColors[p.color] || '#d9dfd5';
  return `<article class="product-card"><div class="product-visual" style="--accent:${escapeHtml(p.accent)}"><span class="product-tag">${escapeHtml(p.category)}</span><span class="product-rating">★ ${Number(p.rating).toFixed(1)}</span><div class="product-art-shirt" style="--fabric:${color}"></div></div><div class="card-body"><div class="card-category">${escapeHtml(p.style)}</div><div class="card-title-row"><h3>${escapeHtml(p.name)}</h3><div class="price">${formatPrice(p.price)} ${p.original_price?`<span class="old-price">${formatPrice(p.original_price)}</span>`:''}</div></div><p>${escapeHtml(p.description)}</p><div class="card-meta"><span class="meta-chip">${escapeHtml(p.color)}</span><span class="meta-chip">${escapeHtml(p.fit)}</span></div><button class="talk-card-btn" data-talk-id="${p.id}"><span>✳</span> Talk to this product</button></div></article>`;
}
async function loadProducts() {
  const grid = $('productGrid');
  try {
    allProducts = await api('/products');
    renderProducts();
  } catch (error) {
    grid.innerHTML = `<div class="empty-state">Couldn't load products. Check that the backend is running, then refresh.</div>`;
    toast(error.message);
  }
}
function renderProducts() {
  const search = $('searchInput').value.trim().toLowerCase();
  const filtered = allProducts.filter(p => (activeCategory === 'all' || p.category.toLowerCase() === activeCategory.toLowerCase()) && (!search || `${p.name} ${p.category} ${p.material} ${p.color} ${p.style} ${p.occasions}`.toLowerCase().includes(search)));
  $('productGrid').innerHTML = filtered.length ? filtered.map(productCard).join('') : '<div class="empty-state">No products found. Try another search.</div>';
  document.querySelectorAll('[data-talk-id]').forEach(button => button.addEventListener('click', () => openTalk(Number(button.dataset.talkId))));
}
function openTalk(id) {
  activeProduct = allProducts.find(p => p.id === id);
  if (!activeProduct) return;
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  $('modalProductName').textContent = activeProduct.name;
  $('modalPrice').textContent = formatPrice(activeProduct.price);
  $('characterShirt').style.setProperty('--character-color', fabricColors[activeProduct.color] || '#d4a15e');
  $('miniFacts').innerHTML = [`${activeProduct.color}`, activeProduct.fit, activeProduct.material.split(';')[0]].map(f => `<span class="mini-fact">${escapeHtml(f)}</span>`).join('');
  $('originNote').textContent = activeProduct.manufactured_in ? `ⓘ Origin listed as ${activeProduct.manufactured_in}${activeProduct.origin_verified ? ' (marked verified in demo data).' : ' (not independently verified).'}` : 'ⓘ Manufacturing origin is not provided in this product listing.';
  $('conversationLog').innerHTML = `<div class="welcome-message"><span class="tiny-spark">✳</span><div><b>Hey there! I'm ${escapeHtml(activeProduct.name)}.</b><p>Ask me about my material, fit, care, price, or where I'm made.</p></div></div>`;
  $('characterStatus').textContent = `${activeProduct.name} is here`;
  $('questionInput').value = '';
  $('talkModal').classList.add('open'); $('talkModal').setAttribute('aria-hidden','false'); document.body.style.overflow='hidden';
  $('characterStage').classList.remove('speaking'); $('speechWave').classList.remove('active');
}
function closeTalk() {
  $('talkModal').classList.remove('open'); $('talkModal').setAttribute('aria-hidden','true'); document.body.style.overflow='';
  if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  $('characterShirt').classList.remove('speaking'); $('speechWave').classList.remove('active');
}
function addMessage(kind, text, sources=[]) {
  const log = $('conversationLog');
  const wrapper = document.createElement('div'); wrapper.className = `message ${kind}`;
  const avatar = document.createElement('span'); avatar.className = 'message-avatar'; avatar.textContent = kind === 'user' ? '☺' : '✳';
  const body = document.createElement('div'); body.style.minWidth='0';
  const content = document.createElement('div'); content.className='message-text'; content.textContent=text;
  body.appendChild(content);
  if (kind === 'assistant' && sources.length) { const note=document.createElement('div'); note.className='source-note'; note.textContent=`Product facts used: ${sources.join(', ')}`; body.appendChild(note); }
  wrapper.append(avatar, body); log.appendChild(wrapper); log.scrollTop=log.scrollHeight;
  return wrapper;
}
function speak(text) {
  if (!voiceEnabled || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.96; utterance.pitch = 1.08;
  utterance.onstart = () => { $('characterShirt').classList.add('speaking'); $('speechWave').classList.add('active'); $('characterStatus').textContent='Talking to you…'; };
  utterance.onend = utterance.onerror = () => { $('characterShirt').classList.remove('speaking'); $('speechWave').classList.remove('active'); if(activeProduct) $('characterStatus').textContent=`${activeProduct.name} is listening`; };
  window.speechSynthesis.speak(utterance);
}
async function sendQuestion(question) {
  if (!activeProduct || busy || !question.trim()) return;
  const message = question.trim();
  addMessage('user', message); $('questionInput').value=''; busy=true;
  const submit = $('talkForm').querySelector('.send-btn'); submit.disabled=true; submit.textContent='…';
  const pending = addMessage('assistant', 'Let me think about that…');
  try {
    const result = await api(`/talk/${activeProduct.id}`, {method:'POST', body:JSON.stringify({message})});
    pending.querySelector('.message-text').textContent = result.answer;
    if (result.sources?.length) { const note=document.createElement('div'); note.className='source-note'; note.textContent=`Product facts used: ${result.sources.join(', ')}`; pending.children[1].appendChild(note); }
    $('conversationLog').scrollTop=$('conversationLog').scrollHeight;
    speak(result.answer);
  } catch (error) {
    pending.querySelector('.message-text').textContent = `I couldn't reach my product information just now. ${error.message}`;
  } finally { busy=false; submit.disabled=false; submit.textContent='↑'; $('questionInput').focus(); }
}
function toast(message) { const el=$('toast'); el.textContent=message; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),2600); }
function setupVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const button = $('micBtn');
  if (!SpeechRecognition) { button.title='Voice input is not supported in this browser. You can still hear spoken answers.'; button.addEventListener('click',()=>toast('Voice input works in supported browsers such as Chrome.')); return; }
  const recognition = new SpeechRecognition(); recognition.lang='en-IN'; recognition.interimResults=false; recognition.maxAlternatives=1;
  button.addEventListener('click',()=>{ try { recognition.start(); button.classList.add('listening'); } catch (_) { toast('Microphone is already listening.'); } });
  recognition.onresult = event => { $('questionInput').value=event.results[0][0].transcript; $('questionInput').focus(); };
  recognition.onend = () => button.classList.remove('listening');
  recognition.onerror = () => { button.classList.remove('listening'); toast('Could not hear that. Check microphone permission and try again.'); };
}
$('searchInput').addEventListener('input', renderProducts);
$('filters').addEventListener('click', event => { const button=event.target.closest('[data-category]'); if(!button)return; activeCategory=button.dataset.category; document.querySelectorAll('.filter').forEach(b=>b.classList.toggle('active',b===button)); renderProducts(); });
$('closeModal').addEventListener('click',closeTalk);
$('talkModal').addEventListener('click',event=>{if(event.target===$('talkModal'))closeTalk();});
document.addEventListener('keydown',event=>{if(event.key==='Escape')closeTalk();});
$('talkForm').addEventListener('submit',event=>{event.preventDefault();sendQuestion($('questionInput').value);});
$('quickQuestions').addEventListener('click',event=>{const button=event.target.closest('button');if(button)sendQuestion(button.textContent);});
$('voiceToggle').addEventListener('click',()=>{voiceEnabled=!voiceEnabled;$('voiceToggle').textContent=voiceEnabled?'🔊 Voice on':'🔇 Voice off';if(!voiceEnabled&&'speechSynthesis'in window)window.speechSynthesis.cancel();});
setupVoiceInput(); loadProducts();
