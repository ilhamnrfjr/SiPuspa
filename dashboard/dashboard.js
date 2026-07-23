const API_URL = 'http://localhost:5000/api';
let authToken    = localStorage.getItem('admin_token');
let analyticsData = null;
let allIntents   = [];
let sessionsData  = [];
let allSessions   = [];
let charts = {};

// ─── INIT ─────────────────────────────────────────────────────────────────────
window.addEventListener('load', () => {
    if (authToken) verifyAndLoadDashboard();
    else showLoginPage();
});

async function verifyAndLoadDashboard() {
    try {
        const res = await fetch(`${API_URL}/auth/verify`, { headers: auth() });
        if (res.ok) {
            const data = await res.json();
                                    document.getElementById('adminName').textContent = data.user.full_name;
            showDashboard();
            loadDashboard();
        } else { localStorage.removeItem('admin_token'); showLoginPage(); }
    } catch { showLoginPage(); }
}

// Sembunyikan tab Users jika bukan superadmin

// ─── HELPERS ──────────────────────────────────────────────────────────────────
function auth()     { return { 'Authorization': `Bearer ${authToken}` }; }
function authJson() { return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` }; }
function escapeHtml(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }

// ─── LOGIN / LOGOUT ───────────────────────────────────────────────────────────
async function handleLogin(e) {
    e.preventDefault();
    const loginBtn = document.getElementById('loginBtn');
    const errorDiv = document.getElementById('loginError');
    loginBtn.disabled = true; loginBtn.textContent = 'Logging in...';
    errorDiv.classList.add('hidden');
    try {
        const res  = await fetch(`${API_URL}/auth/login`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ username: document.getElementById('loginUsername').value, password: document.getElementById('loginPassword').value })
        });
        const data = await res.json();
        if (res.ok) {
            authToken   = data.token;
                        localStorage.setItem('admin_token', authToken);
                        document.getElementById('adminName').textContent = data.user.full_name;
            showDashboard();
            loadDashboard();
        } else { errorDiv.textContent = data.message || 'Login gagal'; errorDiv.classList.remove('hidden'); }
    } catch { errorDiv.textContent = 'Tidak dapat terhubung ke server.'; errorDiv.classList.remove('hidden'); }
    finally { loginBtn.disabled = false; loginBtn.textContent = 'Login'; }
}

function handleLogout() {
    if (!confirm('Yakin ingin logout?')) return;
    fetch(`${API_URL}/auth/logout`, { method:'POST', headers: auth() });
    localStorage.removeItem('admin_token'); localStorage.removeItem('admin_role');
    authToken = null; showLoginPage();
}

function showLoginPage()  { document.getElementById('loginPage').style.display='flex'; document.getElementById('mainDashboard').style.display='none'; }
function showDashboard()  { document.getElementById('loginPage').style.display='none'; document.getElementById('mainDashboard').style.display='block'; }

// ─── LOAD ─────────────────────────────────────────────────────────────────────
async function loadDashboard() {
    await Promise.all([ fetchAnalytics(), fetchLogs(), fetchIntentsForManagement() ]);
}
async function refreshData() { await loadDashboard(); alert('Data direfresh! 🔄'); }

// ─── ANALYTICS ────────────────────────────────────────────────────────────────
async function fetchAnalytics() {
    try {
        const [s,h,c] = await Promise.all([
            fetch(`${API_URL}/admin/analytics/summary`,    { headers: auth() }),
            fetch(`${API_URL}/admin/analytics/hourly`,     { headers: auth() }),
            fetch(`${API_URL}/admin/analytics/confidence`, { headers: auth() })
        ]);
        analyticsData        = await s.json();
        const hourlyData     = h.ok ? (await h.json()).hourly           : [];
        const confidenceData = c.ok ? (await c.json()).confidence_stats : [];
        updateStatsCards();
        updateCharts(hourlyData, confidenceData);
    } catch(err) { console.error('fetchAnalytics:', err); }
}

function updateStatsCards() {
    document.getElementById('totalConversations').textContent = analyticsData.total_conversations || 0;
    document.getElementById('totalMessages').textContent      = analyticsData.total_messages || 0;
    document.getElementById('avgResponseTime').textContent    = `${analyticsData.avg_response_time || 0}s`;
    document.getElementById('avgConfidence').textContent      = `${Math.round((analyticsData.avg_confidence||0)*100)}%`;
}

function genColors(n) { return Array.from({length:n},(_,i)=>`hsl(${Math.round((i/Math.max(n,1))*300)+30},65%,55%)`); }

function updateCharts(hourlyData, confidenceData) {
    Object.values(charts).forEach(c=>c&&c.destroy()); charts={};
    // 1. Line
    charts.messages = new Chart(document.getElementById('messagesChart').getContext('2d'),{
        type:'line', data:{labels:(analyticsData.messages_per_day||[]).map(d=>d.date),datasets:[{label:'Pesan',data:(analyticsData.messages_per_day||[]).map(d=>d.count),borderColor:'#667eea',backgroundColor:'rgba(102,126,234,0.1)',tension:0.4,fill:true,pointRadius:4}]},
        options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{precision:0}}}}
    });
    // 2. Bar frekuensi intent
    const topI = analyticsData.top_intents||[];
    charts.intents = new Chart(document.getElementById('intentsChart').getContext('2d'),{
        type:'bar', data:{labels:topI.map(i=>i.intent),datasets:[{label:'Jumlah',data:topI.map(i=>i.count),backgroundColor:genColors(topI.length),borderRadius:5}]},
        options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{maxRotation:45,font:{size:10}}},y:{beginAtZero:true,ticks:{precision:0}}}}
    });
    // 3. Hourly
    if (hourlyData.length) {
        const mx = Math.max(...hourlyData.map(h=>h.count),1);
        charts.hourly = new Chart(document.getElementById('hourlyChart').getContext('2d'),{
            type:'bar', data:{labels:hourlyData.map(h=>`${String(h.hour).padStart(2,'0')}:00`),datasets:[{data:hourlyData.map(h=>h.count),backgroundColor:hourlyData.map(h=>`rgba(102,126,234,${0.15+h.count/mx*0.85})`),borderRadius:3}]},
            options:{responsive:true,plugins:{legend:{display:false},tooltip:{callbacks:{title:i=>`Pukul ${i[0].label}`,label:i=>`${i.raw} pesan`}}},scales:{x:{ticks:{font:{size:9},maxRotation:0}},y:{beginAtZero:true,ticks:{precision:0}}}}
        });
    }
    // 4. Confidence
    if (confidenceData.length) {
        charts.confidence = new Chart(document.getElementById('confidenceChart').getContext('2d'),{
            type:'bar', data:{labels:confidenceData.map(d=>d.intent),datasets:[{data:confidenceData.map(d=>Math.round(d.avg_confidence*100)),backgroundColor:confidenceData.map(d=>d.avg_confidence>=0.8?'hsl(145,60%,50%)':d.avg_confidence>=0.6?'hsl(45,85%,50%)':'hsl(0,70%,55%)'),borderRadius:3}]},
            options:{indexAxis:'y',responsive:true,plugins:{legend:{display:false},tooltip:{callbacks:{label:i=>[`Confidence: ${i.raw}%`,`Total: ${confidenceData[i.dataIndex].count} pesan`]}}},scales:{x:{beginAtZero:true,max:100,ticks:{callback:v=>`${v}%`}},y:{ticks:{font:{size:10}}}}}
        });
    }
    updateCoverageTable();
}

function updateCoverageTable() {
    const el = document.getElementById('coverageTableBody'); if(!el) return;
    const used = new Map((analyticsData?.top_intents||[]).map(i=>[i.intent,i.count]));
    const rows = allIntents.map(intent=>{
        const name  = intent.intent_name || '';
        const count = used.get(name) ?? 0;
        const badge = count>0
            ? `<span class="px-2 py-1 text-xs font-semibold bg-green-100 text-green-700 rounded-full">✅ Aktif</span>`
            : `<span class="px-2 py-1 text-xs font-semibold bg-red-100 text-red-600 rounded-full">⚠️ Belum dipanggil</span>`;
        return `<tr class="hover:bg-gray-50 border-b border-gray-100">
            <td class="px-4 py-3 text-sm font-medium text-gray-800">${name}</td>
            <td class="px-4 py-3 text-sm text-gray-500">${(intent.patterns||[]).length} patterns</td>
            <td class="px-4 py-3 text-sm font-bold text-purple-700">${count.toLocaleString()}</td>
            <td class="px-4 py-3">${badge}</td></tr>`;
    });
    const never = allIntents.filter(i=>!used.has(i.intent_name)).length;
    document.getElementById('coverageStats').textContent = `${allIntents.length} terdaftar · ${used.size} aktif · ${never} belum dipanggil`;
    el.innerHTML = rows.join('') || '<tr><td colspan="4" class="px-4 py-8 text-center text-gray-400">Belum ada data intent</td></tr>';
}

// ─── SESSIONS / LOGS ──────────────────────────────────────────────────────────
async function fetchLogs() {
    try {
        const res  = await fetch(`${API_URL}/admin/logs/sessions`, { headers: auth() });
        const data = await res.json();
        sessionsData = data.sessions||[]; allSessions = [...sessionsData];
        updateSessionsTable(); updateIntentFilterFromSessions();
    } catch(err) { console.error('fetchLogs:', err); }
}

function updateSessionsTable() {
    const tbody = document.getElementById('logsTableBody');
    if (!sessionsData.length) {
        tbody.innerHTML='<tr><td colspan="5" class="px-4 py-8 text-center text-gray-400">Belum ada percakapan</td></tr>';
        document.getElementById('logsCount').textContent='0 session'; return;
    }
    tbody.innerHTML = sessionsData.map(s=>{
        const d=new Date(s.first_time), dur=new Date(s.last_time)-d;
        const durStr=dur<60000?`${Math.round(dur/1000)}d`:`${Math.round(dur/60000)} mnt`;
        const tags=s.intents_used.slice(0,3).map(i=>`<span class="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full">${i}</span>`).join('');
        const extra=s.intents_used.length>3?`<span class="text-xs text-gray-400">+${s.intents_used.length-3} lagi</span>`:'';
        return `<tr class="hover:bg-purple-50 cursor-pointer border-b border-gray-100" onclick="openSessionModal('${s.session_id}')">
            <td class="px-4 py-3"><div class="text-sm font-medium text-gray-800">${d.toLocaleDateString('id-ID',{day:'2-digit',month:'short',year:'numeric'})}</div><div class="text-xs text-gray-400">${d.toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'})} · ±${durStr}</div></td>
            <td class="px-4 py-3"><span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-sm">${s.total_messages}</span></td>
            <td class="px-4 py-3"><div class="flex flex-wrap gap-1">${tags}${extra}</div></td>
            <td class="px-4 py-3 text-xs text-gray-400 font-mono">${s.session_id.substring(0,12)}...</td>
            <td class="px-4 py-3" onclick="event.stopPropagation()"><button onclick="deleteSession('${s.session_id}')" class="px-3 py-1.5 bg-red-100 text-red-600 rounded-lg text-xs hover:bg-red-200">🗑️ Hapus</button></td>
        </tr>`;
    }).join('');
    document.getElementById('logsCount').textContent=`${sessionsData.length} session · ${sessionsData.reduce((a,s)=>a+s.total_messages,0)} total pesan`;
}

function updateIntentFilterFromSessions() {
    const sel=document.getElementById('intentFilter');
    const intents=[...new Set(allSessions.flatMap(s=>s.intents_used))].sort();
    sel.innerHTML='<option value="all">Semua Intent</option>'+intents.map(i=>`<option value="${i}">${i}</option>`).join('');
}


async function openSessionModal(sessionId) {
    const modal=document.getElementById('sessionModal'), content=document.getElementById('sessionModalContent'), title=document.getElementById('sessionModalTitle');
    title.textContent='Memuat...'; content.innerHTML='<div class="flex justify-center py-12"><div class="loading-spinner"></div></div>'; modal.classList.add('active');
    try {
        const res=await fetch(`${API_URL}/admin/logs/session/${sessionId}`,{headers:auth()});
        if(!res.ok){content.innerHTML='<p class="text-center text-red-500 py-8">Gagal memuat.</p>';return;}
        const {messages,summary}=await res.json();
        const fd=new Date(summary.first_time), dur=new Date(summary.last_time)-fd;
        title.textContent=`Detail Session (${summary.total_messages} pesan)`;
        content.innerHTML=`
        <div class="flex flex-wrap gap-3 mb-4 p-3 bg-gray-50 rounded-xl text-xs text-gray-600">
            <span>🕐 ${fd.toLocaleDateString('id-ID',{day:'2-digit',month:'short',year:'numeric'})} ${fd.toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'})}</span>
            <span>⏱️ ±${dur<60000?`${Math.round(dur/1000)}d`:`${Math.round(dur/60000)} mnt`}</span>
            <span>💬 <strong>${summary.total_messages}</strong> pesan</span>
        </div>
        <div class="flex flex-wrap gap-1 mb-4">${summary.intents_used.map(i=>`<span class="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full">${i}</span>`).join('')}</div>
        <div class="space-y-4 max-h-[400px] overflow-y-auto pr-1">
        ${messages.map((msg,idx)=>{
            const ts=new Date(msg.timestamp), cc=msg.confidence>0.8?'text-green-600':msg.confidence>0.5?'text-yellow-600':'text-red-500';
            return `<div class="space-y-2">
                <div class="flex justify-end"><div class="max-w-[80%]">
                    <div class="bg-gradient-to-br from-purple-600 to-blue-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm shadow-sm"><p class="text-sm">${escapeHtml(msg.user_message)}</p></div>
                    <div class="flex justify-end gap-2 mt-1 text-xs"><span class="text-gray-400">${ts.toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}</span><span class="${cc}">${Math.round((msg.confidence||0)*100)}%</span><span class="text-gray-400 bg-gray-100 px-1.5 rounded">${msg.intent||'-'}</span></div>
                </div></div>
                <div class="flex justify-start"><div class="max-w-[80%]">
                    <div class="text-xs text-gray-400 mb-1">🤖 Bot · ${(msg.response_time||0).toFixed(3)}s</div>
                    <div class="bg-gray-100 text-gray-800 px-4 py-3 rounded-2xl rounded-tl-sm shadow-sm"><p class="text-sm whitespace-pre-wrap">${escapeHtml(msg.bot_response)}</p></div>
                </div></div>
                ${idx<messages.length-1?'<hr class="border-gray-100">':''}
            </div>`;
        }).join('')}
        </div>
        <div class="mt-4 pt-4 border-t border-gray-100 flex justify-end">
            <button onclick="deleteSession('${sessionId}',true)" class="px-4 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600">🗑️ Hapus Session Ini</button>
        </div>`;
    } catch(err){content.innerHTML=`<p class="text-center text-red-500 py-8">Error: ${err.message}</p>`;}
}

async function deleteSession(id, fromModal=false) {
    if(!confirm('Hapus semua pesan dalam session ini?'))return;
    const res=await fetch(`${API_URL}/admin/logs/session/${id}`,{method:'DELETE',headers:auth()});
    if(res.ok){if(fromModal)closeModal('sessionModal');await fetchLogs();await fetchAnalytics();}
    else alert('Gagal: '+(await res.json()).error);
}



// ─── MANAGE INTENTS ───────────────────────────────────────────────────────────
async function fetchIntentsForManagement() {
    const res=await fetch(`${API_URL}/admin/intents`,{headers:auth()});
    const data=await res.json();
    allIntents=data.intents||[]; updateManageIntentsTable(); updateCoverageTable();
}

function updateManageIntentsTable() {
    const tbody=document.getElementById('manageIntentsBody');
    if(!allIntents.length){tbody.innerHTML='<tr><td colspan="3" class="px-4 py-8 text-center text-gray-400">Belum ada intent</td></tr>';return;}
    tbody.innerHTML=allIntents.map(i=>`<tr class="hover:bg-gray-50 border-b border-gray-100">
        <td class="px-4 py-3 font-medium text-sm text-gray-800">${i.intent_name}</td>
        <td class="px-4 py-3 text-sm text-gray-500">${(i.patterns||[]).length} patterns</td>
        <td class="px-4 py-3 flex gap-2">
            <button onclick='editIntent(${JSON.stringify(i).replace(/'/g,"&apos;")})' class="px-3 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600">✏️ Edit</button>
            <button onclick="deleteIntent('${i.intent_name}')" class="px-3 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600">🗑️ Hapus</button>
        </td></tr>`).join('');
}

function showAddIntentModal() {
    document.getElementById('intentModalTitle').textContent='Tambah Intent Baru';
    ['intentName','intentPatterns','intentResponseText','intentQuickReplies','editingIntent'].forEach(id=>document.getElementById(id).value='');
    document.getElementById('intentModal').classList.add('active');
}

function editIntent(intent) {
    document.getElementById('intentModalTitle').textContent='Edit Intent';
    document.getElementById('intentName').value          = intent.intent_name||'';
    document.getElementById('intentPatterns').value      = (intent.patterns||[]).join('\n');
    document.getElementById('intentResponseText').value  = intent.response_text||'';
    document.getElementById('intentQuickReplies').value  = (intent.quick_replies||[]).join(', ');
    document.getElementById('editingIntent').value       = intent.intent_name||'';
    document.getElementById('intentModal').classList.add('active');
}

async function handleSaveIntent(e) {
    e.preventDefault();
    const name     = document.getElementById('intentName').value.trim();
    const patterns = document.getElementById('intentPatterns').value.split('\n').map(p=>p.trim()).filter(Boolean);
    const respText = document.getElementById('intentResponseText').value.trim();
    const qr       = document.getElementById('intentQuickReplies').value.split(',').map(x=>x.trim()).filter(Boolean);
    const editing  = document.getElementById('editingIntent').value;
    if(!name||!patterns.length||!respText){alert('Nama intent, patterns, dan teks jawaban wajib diisi!');return;}
    const url    = editing?`${API_URL}/admin/intents/${editing}`:`${API_URL}/admin/intents`;
    const method = editing?'PUT':'POST';
    const res    = await fetch(url,{method,headers:authJson(),body:JSON.stringify({intent_name:name,patterns,response_text:respText,quick_replies:qr})});
    if(res.ok){alert(editing?'Intent diupdate ✅':'Intent ditambahkan ✅');closeModal('intentModal');fetchIntentsForManagement();}
    else alert('Error: '+(await res.json()).error);
}

async function deleteIntent(name) {
    if(!confirm(`Hapus intent "${name}"?`))return;
    const res=await fetch(`${API_URL}/admin/intents/${name}`,{method:'DELETE',headers:auth()});
    if(res.ok){alert('Dihapus ✅');fetchIntentsForManagement();}
    else alert('Gagal: '+(await res.json()).error);
}

// ─── TAB SWITCHING ────────────────────────────────────────────────────────────
const TAB_IDS  = ['overview', 'logs', 'manage'];
const TAB_LOAD = {};

function switchTab(tab) {
    TAB_IDS.forEach(t => {
        const el  = document.getElementById(t + 'Tab');
        const btn = document.getElementById('tab' + t.charAt(0).toUpperCase() + t.slice(1));
        if (el)  el.style.display  = t === tab ? 'block' : 'none';
        if (btn) btn.className = 'py-4 px-3 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ' +
                                 (t === tab ? 'tab-active' : 'tab-inactive');
    });
    if (TAB_LOAD[tab]) TAB_LOAD[tab]();
}

// ─── LOG FILTERS & ACTIONS ────────────────────────────────────────────────────
function filterLogs() {
    const q = document.getElementById('searchInput').value.toLowerCase();
    const f = document.getElementById('intentFilter').value;
    sessionsData = allSessions.filter(s => {
        const mi = f === 'all' || s.intents_used.includes(f);
        const mq = !q || s.session_id.toLowerCase().includes(q) ||
                   s.intents_used.some(i => i.toLowerCase().includes(q));
        return mi && mq;
    });
    updateSessionsTable();
}

async function downloadBackup(fmt) {
    const res = await fetch(`${API_URL}/admin/logs/backup?format=${fmt}`, { headers: auth() });
    if (!res.ok) { alert('Gagal backup'); return; }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `backup_${new Date().toISOString().slice(0, 10)}.${fmt}`;
    a.click();
    URL.revokeObjectURL(url);
}

async function deleteAllLogs() {
    if (!confirm('⚠️ Hapus SEMUA history?\nPastikan sudah backup!\n\nLanjutkan?')) return;
    if (!confirm('Konfirmasi terakhir — hapus semua?')) return;
    const res = await fetch(`${API_URL}/admin/logs/all`, { method: 'DELETE', headers: auth() });
    if (res.ok) {
        alert(`✅ ${(await res.json()).message}`);
        await fetchLogs();
        await fetchAnalytics();
    } else { alert('Gagal.'); }
}