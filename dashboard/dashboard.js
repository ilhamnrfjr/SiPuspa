const API_URL = 'http://localhost:5000/api';
let authToken = localStorage.getItem('admin_token');
let analyticsData = null;
let logsData = [];
let allLogs = [];
let allIntents = [];
let charts = {};

window.addEventListener('load', function() {
    if (authToken) {
        verifyAndLoadDashboard();
    } else {
        showLoginPage();
    }
});

async function verifyAndLoadDashboard() {
    try {
        const response = await fetch(`${API_URL}/auth/verify`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('adminName').textContent = data.user.full_name;
            showDashboard();
            loadDashboard();
        } else {
            localStorage.removeItem('admin_token');
            showLoginPage();
        }
    } catch (error) {
        console.error('Verification failed:', error);
        showLoginPage();
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const loginBtn = document.getElementById('loginBtn');
    const errorDiv = document.getElementById('loginError');

    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';
    errorDiv.classList.add('hidden');

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (response.ok) {
            authToken = data.token;
            localStorage.setItem('admin_token', authToken);
            document.getElementById('adminName').textContent = data.user.full_name;
            showDashboard();
            loadDashboard();
        } else {
            errorDiv.textContent = data.message || 'Login gagal';
            errorDiv.classList.remove('hidden');
        }
    } catch (error) {
        errorDiv.textContent = 'Tidak dapat terhubung ke server. Pastikan backend running.';
        errorDiv.classList.remove('hidden');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
    }
}

function handleLogout() {
    if (confirm('Yakin ingin logout?')) {
        fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        localStorage.removeItem('admin_token');
        authToken = null;
        showLoginPage();
    }
}

function showLoginPage() {
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('mainDashboard').style.display = 'none';
}

function showDashboard() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('mainDashboard').style.display = 'block';
}

async function loadDashboard() {
    await Promise.all([
        fetchAnalytics(),
        fetchLogs(),
        fetchIntentsForManagement()
    ]);
}

// ─── DATA FETCHING ────────────────────────────────────────────────────────────

async function fetchAnalytics() {
    try {
        const [summaryRes, hourlyRes, confidenceRes] = await Promise.all([
            fetch(`${API_URL}/admin/analytics/summary`,    { headers: { 'Authorization': `Bearer ${authToken}` } }),
            fetch(`${API_URL}/admin/analytics/hourly`,     { headers: { 'Authorization': `Bearer ${authToken}` } }),
            fetch(`${API_URL}/admin/analytics/confidence`, { headers: { 'Authorization': `Bearer ${authToken}` } })
        ]);

        analyticsData = await summaryRes.json();
        const hourlyData    = hourlyRes.ok    ? (await hourlyRes.json()).hourly           : [];
        const confidenceData = confidenceRes.ok ? (await confidenceRes.json()).confidence_stats : [];

        updateStatsCards();
        updateCharts(hourlyData, confidenceData);
    } catch (err) {
        console.error('fetchAnalytics error:', err);
    }
}

// sessionsData = list of sessions (1 per session_id)
let sessionsData = [];
let allSessions  = [];

async function fetchLogs() {
    try {
        const res  = await fetch(`${API_URL}/admin/logs/sessions`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await res.json();
        sessionsData = data.sessions || [];
        allSessions  = [...sessionsData];
        updateSessionsTable();
        updateIntentFilterFromSessions();
    } catch (err) {
        console.error('fetchLogs error:', err);
    }
}

async function fetchIntentsForManagement() {
    const response = await fetch(`${API_URL}/admin/intents`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
    });
    const data = await response.json();
    allIntents = data.intents || [];
    updateManageIntentsTable();
}

// ─── STATS CARDS ─────────────────────────────────────────────────────────────

function updateStatsCards() {
    document.getElementById('totalConversations').textContent = analyticsData.total_conversations || 0;
    document.getElementById('totalMessages').textContent      = analyticsData.total_messages || 0;
    document.getElementById('avgResponseTime').textContent    = `${analyticsData.avg_response_time || 0}s`;
    document.getElementById('avgConfidence').textContent      = `${Math.round((analyticsData.avg_confidence || 0) * 100)}%`;
}

// ─── COLOR HELPER ─────────────────────────────────────────────────────────────

function generateColors(count, alpha = 1) {
    return Array.from({ length: count }, (_, i) => {
        const hue = Math.round((i / Math.max(count, 1)) * 300) + 30; // 30-330 deg, hindari merah ganda
        return alpha < 1
            ? `hsla(${hue}, 65%, 55%, ${alpha})`
            : `hsl(${hue}, 65%, 55%)`;
    });
}

// ─── CHARTS ───────────────────────────────────────────────────────────────────

function updateCharts(hourlyData, confidenceData) {
    Object.values(charts).forEach(c => c && c.destroy());
    charts = {};

    drawMessagesPerDayChart();
    drawIntentFrequencyChart();
    drawHourlyHeatmapChart(hourlyData);
    drawConfidenceChart(confidenceData);
}

// 1. Line chart — pesan per hari
function drawMessagesPerDayChart() {
    const ctx = document.getElementById('messagesChart').getContext('2d');
    charts.messages = new Chart(ctx, {
        type: 'line',
        data: {
            labels: (analyticsData.messages_per_day || []).map(d => d.date),
            datasets: [{
                label: 'Pesan',
                data: (analyticsData.messages_per_day || []).map(d => d.count),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.12)',
                tension: 0.4,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

// 2. Bar chart — frekuensi semua intent (dinamis, tanpa slice)
function drawIntentFrequencyChart() {
    const ctx = document.getElementById('intentsChart').getContext('2d');
    const intents = analyticsData.top_intents || [];
    const colors  = generateColors(intents.length);

    charts.intents = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: intents.map(i => i.intent),
            datasets: [{
                label: 'Jumlah Pesan',
                data: intents.map(i => i.count),
                backgroundColor: colors,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { maxRotation: 45, minRotation: 30, font: { size: 11 } } },
                y: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });
}

// 3. Bar chart horizontal — aktivitas per jam (heatmap sederhana)
function drawHourlyHeatmapChart(hourlyData) {
    const ctx = document.getElementById('hourlyChart').getContext('2d');
    if (!ctx || !hourlyData.length) return;

    const maxCount = Math.max(...hourlyData.map(h => h.count), 1);
    const bgColors = hourlyData.map(h => {
        const intensity = h.count / maxCount;
        return `rgba(102, 126, 234, ${0.15 + intensity * 0.85})`;
    });

    charts.hourly = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hourlyData.map(h => `${String(h.hour).padStart(2,'0')}:00`),
            datasets: [{
                label: 'Pesan',
                data: hourlyData.map(h => h.count),
                backgroundColor: bgColors,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => `Pukul ${items[0].label}`,
                        label: (item) => `${item.raw} pesan`
                    }
                }
            },
            scales: {
                x: { ticks: { font: { size: 10 }, maxRotation: 0 } },
                y: { beginAtZero: true, ticks: { precision: 0 } }
            }
        }
    });
}

// 4. Horizontal bar — avg confidence per intent, diurutkan dari terendah
//    Intent dengan confidence rendah = perlu perbaikan patterns
function drawConfidenceChart(confidenceData) {
    const ctx = document.getElementById('confidenceChart').getContext('2d');
    if (!ctx || !confidenceData.length) return;

    // Warna merah→kuning→hijau berdasarkan nilai confidence
    const bgColors = confidenceData.map(d => {
        const v = d.avg_confidence;
        if (v >= 0.8) return 'hsl(145, 60%, 50%)';
        if (v >= 0.6) return 'hsl(45, 85%, 50%)';
        return 'hsl(0, 70%, 55%)';
    });

    charts.confidence = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: confidenceData.map(d => d.intent),
            datasets: [{
                label: 'Avg Confidence',
                data: confidenceData.map(d => Math.round(d.avg_confidence * 100)),
                backgroundColor: bgColors,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',   // horizontal bar
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (item) => {
                            const d = confidenceData[item.dataIndex];
                            return [`Confidence: ${item.raw}%`, `Total pesan: ${d.count}`];
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { callback: v => `${v}%` }
                },
                y: { ticks: { font: { size: 11 } } }
            }
        }
    });
}

// ─── INTENT COVERAGE TABLE ────────────────────────────────────────────────────
// Dipanggil setelah allIntents (dari manage) dan analyticsData tersedia

function updateCoverageTable() {
    const container = document.getElementById('coverageTableBody');
    if (!container) return;

    const usedIntents = new Map(
        (analyticsData?.top_intents || []).map(i => [i.intent, i.count])
    );

    const rows = allIntents.map(intent => {
        const count  = usedIntents.get(intent.intent) ?? 0;
        const status = count > 0
            ? `<span class="px-2 py-1 text-xs font-semibold bg-green-100 text-green-700 rounded-full">✅ Aktif</span>`
            : `<span class="px-2 py-1 text-xs font-semibold bg-red-100 text-red-600 rounded-full">⚠️ Belum pernah dipanggil</span>`;

        return `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-sm font-medium text-gray-800">${intent.intent}</td>
                <td class="px-4 py-3 text-sm text-gray-500">${intent.patterns.length} patterns</td>
                <td class="px-4 py-3 text-sm font-bold text-purple-700">${count.toLocaleString()}</td>
                <td class="px-4 py-3">${status}</td>
            </tr>`;
    });

    const neverUsed = allIntents.filter(i => !usedIntents.has(i.intent)).length;
    document.getElementById('coverageStats').textContent =
        `${allIntents.length} intent terdaftar • ${usedIntents.size} pernah dipakai • ${neverUsed} belum pernah dipanggil`;

    container.innerHTML = rows.length
        ? rows.join('')
        : '<tr><td colspan="4" class="px-4 py-8 text-center text-gray-400">Belum ada data intent</td></tr>';
}

// ─── SESSIONS TABLE (1 baris = 1 session) ────────────────────────────────────

function updateSessionsTable() {
    const tbody = document.getElementById('logsTableBody');

    if (sessionsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-8 text-center text-gray-400">Belum ada percakapan</td></tr>';
        document.getElementById('logsCount').textContent = '0 session';
        return;
    }

    tbody.innerHTML = sessionsData.map(session => {
        const date    = new Date(session.first_time);
        const dateStr = date.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
        const timeStr = date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });

        const durMs  = new Date(session.last_time) - date;
        const durStr = durMs < 60000
            ? `${Math.round(durMs / 1000)}d`
            : `${Math.round(durMs / 60000)} mnt`;

        const intentTags = session.intents_used.slice(0, 3).map(i =>
            `<span class="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full">${i}</span>`
        ).join('');
        const extraIntents = session.intents_used.length > 3
            ? `<span class="text-xs text-gray-400">+${session.intents_used.length - 3} lagi</span>` : '';

        return `
            <tr class="hover:bg-purple-50 transition-colors cursor-pointer border-b border-gray-100"
                onclick="openSessionModal('${session.session_id}')"
                title="Klik untuk lihat detail percakapan">
                <td class="px-4 py-3">
                    <div class="text-sm font-medium text-gray-800">${dateStr}</div>
                    <div class="text-xs text-gray-400">${timeStr} • durasi ±${durStr}</div>
                </td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-sm">
                        ${session.total_messages}
                    </span>
                </td>
                <td class="px-4 py-3">
                    <div class="flex flex-wrap gap-1">${intentTags}${extraIntents}</div>
                </td>
                <td class="px-4 py-3 text-xs text-gray-400 font-mono">${session.session_id.substring(0,12)}...</td>
                <td class="px-4 py-3" onclick="event.stopPropagation()">
                    <button onclick="deleteSession('${session.session_id}')"
                            class="px-3 py-1.5 bg-red-100 text-red-600 rounded-lg text-xs font-medium hover:bg-red-200 transition-colors">
                        🗑️ Hapus
                    </button>
                </td>
            </tr>`;
    }).join('');

    document.getElementById('logsCount').textContent =
        `${sessionsData.length} session • ${sessionsData.reduce((a, s) => a + s.total_messages, 0)} total pesan`;
}


function updateIntentFilterFromSessions() {
    const select  = document.getElementById('intentFilter');
    const intents = [...new Set(allSessions.flatMap(s => s.intents_used))].sort();
    select.innerHTML = '<option value="all">Semua Intent</option>' +
        intents.map(i => `<option value="${i}">${i}</option>`).join('');
}

function filterLogs() {
    const searchQuery  = document.getElementById('searchInput').value.toLowerCase();
    const intentFilter = document.getElementById('intentFilter').value;

    sessionsData = allSessions.filter(session => {
        const matchesIntent = intentFilter === 'all' || session.intents_used.includes(intentFilter);
        return matchesIntent;
        // Note: search by session_id prefix jika ada query
    });

    // Filter by search (cocokkan session_id)
    if (searchQuery) {
        sessionsData = sessionsData.filter(s =>
            s.session_id.toLowerCase().includes(searchQuery) ||
            s.intents_used.some(i => i.toLowerCase().includes(searchQuery))
        );
    }

    updateSessionsTable();
}


// ─── MANAGE INTENTS TABLE ─────────────────────────────────────────────────────

function updateManageIntentsTable() {
    const tbody = document.getElementById('manageIntentsBody');

    if (allIntents.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="px-4 py-8 text-center text-gray-500">Belum ada intent</td></tr>';
        return;
    }

    tbody.innerHTML = allIntents.map(intent => `
        <tr class="hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">${intent.intent}</td>
            <td class="px-4 py-3 text-sm text-gray-600">${intent.patterns.length} patterns</td>
            <td class="px-4 py-3 text-sm">${intent.response_key}</td>
            <td class="px-4 py-3">
                <button onclick='editIntent(${JSON.stringify(intent).replace(/'/g, "&apos;")})'
                        class="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 mr-2">
                    ✏️ Edit
                </button>
                <button onclick="deleteIntent('${intent.intent}')"
                        class="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600">
                    🗑️ Delete
                </button>
            </td>
        </tr>
    `).join('');

    // Perbarui tabel coverage setiap kali daftar intent berubah
    updateCoverageTable();
}

// ─── FILTERS ──────────────────────────────────────────────────────────────────

function filterLogs() {
    const searchQuery  = document.getElementById('searchInput').value.toLowerCase();
    const intentFilter = document.getElementById('intentFilter').value;

    logsData = allLogs.filter(log => {
        const matchesSearch = log.user_message.toLowerCase().includes(searchQuery) ||
                              log.bot_response.toLowerCase().includes(searchQuery);
        const matchesIntent = intentFilter === 'all' || log.intent === intentFilter;
        return matchesSearch && matchesIntent;
    });

    updateLogsTable();
}

// ─── TAB SWITCHING ────────────────────────────────────────────────────────────

function switchTab(tab) {
    ['overviewTab', 'logsTab', 'manageTab'].forEach(id => {
        document.getElementById(id).style.display = 'none';
    });
    ['tabOverview', 'tabLogs', 'tabManage'].forEach(id => {
        document.getElementById(id).className =
            'py-4 px-2 border-b-2 font-medium text-sm transition-colors tab-inactive';
    });

    document.getElementById(tab + 'Tab').style.display = 'block';
    document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1)).className =
        'py-4 px-2 border-b-2 font-medium text-sm transition-colors tab-active';
}

function refreshData() {
    loadDashboard();
    alert('Data berhasil direfresh! 🔄');
}

// ─── MODAL & CRUD ─────────────────────────────────────────────────────────────

async function showAddIntentModal() {
    document.getElementById('modalTitle').textContent = 'Tambah Intent & Response Baru';
    ['intentName','intentPatterns','intentResponseKey','intentResponseText','intentEntities','intentQuickReplies','editingIntent']
        .forEach(id => document.getElementById(id).value = '');
    document.getElementById('intentModal').classList.add('active');
}

async function editIntent(intent) {
    document.getElementById('modalTitle').textContent = 'Edit Intent & Response';
    document.getElementById('intentName').value        = intent.intent;
    document.getElementById('intentPatterns').value    = intent.patterns.join('\n');
    document.getElementById('intentResponseKey').value = intent.response_key;
    document.getElementById('intentEntities').value    = (intent.entities || []).join(', ');
    document.getElementById('editingIntent').value     = intent.intent;

    try {
        const response = await fetch(`${API_URL}/admin/responses/${intent.response_key}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('intentResponseText').value  = data.response.text || '';
            document.getElementById('intentQuickReplies').value  = (data.response.quick_replies || []).join(', ');
        }
    } catch (error) {
        console.error('Error loading response:', error);
    }

    document.getElementById('intentModal').classList.add('active');
}

function closeIntentModal() {
    document.getElementById('intentModal').classList.remove('active');
}

async function handleSaveIntent(event) {
    event.preventDefault();

    const intentName  = document.getElementById('intentName').value.trim();
    const patterns    = document.getElementById('intentPatterns').value.split('\n').map(p => p.trim()).filter(Boolean);
    const responseKey = document.getElementById('intentResponseKey').value.trim();
    const responseText = document.getElementById('intentResponseText').value.trim();
    const entities    = document.getElementById('intentEntities').value.split(',').map(e => e.trim()).filter(Boolean);
    const quickReplies = document.getElementById('intentQuickReplies').value.split(',').map(q => q.trim()).filter(Boolean);
    const editing     = document.getElementById('editingIntent').value;

    if (!intentName || patterns.length === 0 || !responseKey || !responseText) {
        alert('Semua field bertanda * harus diisi!');
        return;
    }

    try {
        const intentUrl    = editing ? `${API_URL}/admin/intents/${editing}` : `${API_URL}/admin/intents`;
        const intentMethod = editing ? 'PUT' : 'POST';

        const intentRes = await fetch(intentUrl, {
            method: intentMethod,
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` },
            body: JSON.stringify({ intent: intentName, patterns, response_key: responseKey, entities })
        });

        if (!intentRes.ok) { alert('Error menyimpan intent: ' + (await intentRes.json()).error); return; }

        const responseRes = await fetch(`${API_URL}/admin/responses/${responseKey}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}` },
            body: JSON.stringify({ text: responseText, quick_replies: quickReplies })
        });

        if (!responseRes.ok) { alert('Error menyimpan response: ' + (await responseRes.json()).error); return; }

        alert(editing ? 'Intent & Response berhasil diupdate! ✅' : 'Intent & Response berhasil ditambahkan! ✅');
        closeIntentModal();
        fetchIntentsForManagement();

    } catch (error) {
        alert('Gagal menyimpan: ' + error.message);
    }
}

async function deleteIntent(intentName) {
    if (!confirm(`Yakin ingin menghapus intent "${intentName}"?\n\nResponse untuk intent ini tidak akan dihapus.`)) return;

    try {
        const response = await fetch(`${API_URL}/admin/intents/${intentName}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            alert('Intent berhasil dihapus! ✅');
            fetchIntentsForManagement();
        } else {
            alert('Gagal menghapus intent: ' + (await response.json()).error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// ─── SESSION DETAIL MODAL ─────────────────────────────────────────────────────

async function openSessionModal(sessionId) {
    const modal   = document.getElementById('sessionModal');
    const content = document.getElementById('sessionModalContent');
    const title   = document.getElementById('sessionModalTitle');

    title.textContent = 'Memuat...';
    content.innerHTML = '<div class="flex justify-center py-12"><div class="loading-spinner"></div></div>';
    modal.classList.add('active');

    try {
        const res = await fetch(`${API_URL}/admin/logs/session/${sessionId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) { content.innerHTML = '<p class="text-center text-red-500 py-8">Gagal memuat data session.</p>'; return; }

        const data = await res.json();
        const { messages, summary } = data;

        const firstDate = new Date(summary.first_time);
        const durMs     = new Date(summary.last_time) - firstDate;
        const durStr    = durMs < 60000 ? `${Math.round(durMs/1000)}d` : `${Math.round(durMs/60000)} menit`;

        title.textContent = `Detail Session (${summary.total_messages} pesan)`;

        content.innerHTML = `
            <div class="flex flex-wrap gap-3 mb-5 p-4 bg-gray-50 rounded-xl text-sm">
                <div class="text-gray-600">🕐 ${firstDate.toLocaleDateString('id-ID', {day:'2-digit',month:'short',year:'numeric'})} ${firstDate.toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'})}</div>
                <div class="text-gray-600">⏱️ Durasi ±${durStr}</div>
                <div class="text-gray-600">💬 <strong>${summary.total_messages}</strong> pesan</div>
            </div>
            <div class="flex flex-wrap gap-2 mb-5">
                <span class="text-xs text-gray-500 self-center">Intent:</span>
                ${summary.intents_used.map(i => `<span class="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">${i}</span>`).join('')}
            </div>
            <div class="space-y-4 max-h-[420px] overflow-y-auto pr-1">
                ${messages.map((msg, idx) => {
                    const ts = new Date(msg.timestamp);
                    const timeStr = ts.toLocaleTimeString('id-ID', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
                    const confColor = msg.confidence > 0.8 ? 'text-green-600' : msg.confidence > 0.5 ? 'text-yellow-600' : 'text-red-500';
                    return `
                    <div class="space-y-2">
                        <div class="flex justify-end">
                            <div class="max-w-[80%]">
                                <div class="bg-gradient-to-br from-purple-600 to-blue-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm shadow-sm">
                                    <p class="text-sm">${escapeHtml(msg.user_message)}</p>
                                </div>
                                <div class="flex justify-end gap-2 mt-1">
                                    <span class="text-xs text-gray-400">${timeStr}</span>
                                    <span class="text-xs ${confColor} font-medium">${Math.round((msg.confidence||0)*100)}%</span>
                                    <span class="text-xs text-gray-400 bg-gray-100 px-1.5 rounded">${msg.intent||'-'}</span>
                                </div>
                            </div>
                        </div>
                        <div class="flex justify-start">
                            <div class="max-w-[80%]">
                                <div class="flex items-center gap-1 mb-1">
                                    <span class="text-sm">🤖</span>
                                    <span class="text-xs text-gray-400">Bot • ${(msg.response_time||0).toFixed(3)}s</span>
                                </div>
                                <div class="bg-gray-100 text-gray-800 px-4 py-3 rounded-2xl rounded-tl-sm shadow-sm">
                                    <p class="text-sm whitespace-pre-wrap">${escapeHtml(msg.bot_response)}</p>
                                </div>
                            </div>
                        </div>
                        ${idx < messages.length - 1 ? '<hr class="border-gray-100">' : ''}
                    </div>`;
                }).join('')}
            </div>
            <div class="mt-5 pt-4 border-t border-gray-100 flex justify-end">
                <button onclick="deleteSession('${sessionId}', true)"
                        class="px-4 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors">
                    🗑️ Hapus Session Ini
                </button>
            </div>`;
    } catch (err) {
        content.innerHTML = `<p class="text-center text-red-500 py-8">Error: ${err.message}</p>`;
    }
}

function closeSessionModal() {
    document.getElementById('sessionModal').classList.remove('active');
}

function escapeHtml(str) {
    return (str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─── DELETE SESSION ───────────────────────────────────────────────────────────

async function deleteSession(sessionId, fromModal = false) {
    if (!confirm('Hapus semua pesan dalam session ini?')) return;
    try {
        const res = await fetch(`${API_URL}/admin/logs/session/${sessionId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (res.ok) {
            if (fromModal) closeSessionModal();
            await fetchLogs();
            await fetchAnalytics();
        } else {
            alert('Gagal menghapus: ' + (await res.json()).error);
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// ─── DELETE ALL LOGS ──────────────────────────────────────────────────────────

async function deleteAllLogs() {
    if (!confirm('⚠️ HAPUS SEMUA HISTORY?\n\nSeluruh log percakapan akan dihapus permanen.\nPastikan sudah backup terlebih dahulu.\n\nLanjutkan?')) return;
    if (!confirm('Konfirmasi terakhir: benar-benar hapus SEMUA history?')) return;
    try {
        const res = await fetch(`${API_URL}/admin/logs/all`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (res.ok) {
            const data = await res.json();
            alert(`✅ ${data.message}`);
            await fetchLogs();
            await fetchAnalytics();
        } else {
            alert('Gagal menghapus logs');
        }
    } catch (err) {
        alert('Error: ' + err.message);
    }
}

// ─── BACKUP CSV ───────────────────────────────────────────────────────────────

async function downloadBackup(format) {
    try {
        const res = await fetch(`${API_URL}/admin/logs/backup?format=${format}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!res.ok) { alert('Gagal membuat backup'); return; }
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `chatbot_logs_backup_${new Date().toISOString().slice(0,10)}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (err) {
        alert('Error backup: ' + err.message);
    }
}