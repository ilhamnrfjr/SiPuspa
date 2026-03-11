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
    await Promise.all([fetchAnalytics(), fetchLogs(), fetchIntentsForManagement()]);
}

async function fetchAnalytics() {
    const response = await fetch(`${API_URL}/admin/analytics/summary`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
    });
    analyticsData = await response.json();
    updateStatsCards();
    updateCharts();
    updateIntentsAnalysis();
}

async function fetchLogs() {
    const response = await fetch(`${API_URL}/admin/logs?limit=100`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
    });
    const data = await response.json();
    logsData = data.logs || [];
    allLogs = [...logsData];
    updateLogsTable();
    updateIntentFilter();
}

async function fetchIntentsForManagement() {
    const response = await fetch(`${API_URL}/admin/intents`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
    });
    const data = await response.json();
    allIntents = data.intents || [];
    updateManageIntentsTable();
}

function updateStatsCards() {
    document.getElementById('totalConversations').textContent = analyticsData.total_conversations || 0;
    document.getElementById('totalMessages').textContent = analyticsData.total_messages || 0;
    document.getElementById('avgResponseTime').textContent = `${analyticsData.avg_response_time || 0}s`;
    document.getElementById('avgConfidence').textContent = `${Math.round((analyticsData.avg_confidence || 0) * 100)}%`;
}

function updateCharts() {
    // Destroy existing charts
    Object.values(charts).forEach(chart => chart && chart.destroy());
    
    // Messages per day chart
    const messagesCtx = document.getElementById('messagesChart').getContext('2d');
    charts.messages = new Chart(messagesCtx, {
        type: 'line',
        data: {
            labels: (analyticsData.messages_per_day || []).map(d => d.date),
            datasets: [{
                label: 'Pesan',
                data: (analyticsData.messages_per_day || []).map(d => d.count),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // Top intents bar chart
    const intentsCtx = document.getElementById('intentsChart').getContext('2d');
    const topIntents = (analyticsData.top_intents || []).slice(0, 10);
    charts.intents = new Chart(intentsCtx, {
        type: 'bar',
        data: {
            labels: topIntents.map(i => i.intent),
            datasets: [{
                label: 'Jumlah',
                data: topIntents.map(i => i.count),
                backgroundColor: '#667eea'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // Pie chart
    const pieCtx = document.getElementById('pieChart').getContext('2d');
    const topIntentsPie = (analyticsData.top_intents || []).slice(0, 6);
    charts.pie = new Chart(pieCtx, {
        type: 'pie',
        data: {
            labels: topIntentsPie.map(i => i.intent),
            datasets: [{
                data: topIntentsPie.map(i => i.count),
                backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function updateIntentsAnalysis() {
    const container = document.getElementById('intentsList');
    const intents = analyticsData.top_intents || [];
    
    if (intents.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">Belum ada data intent</p>';
        return;
    }
    
    container.innerHTML = intents.map((intent, index) => {
        const percentage = ((intent.count / analyticsData.total_messages) * 100).toFixed(1);
        return `
            <div class="bg-white rounded-lg p-4 shadow-sm">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-3">
                        <span class="text-2xl font-bold text-gray-300">#${index + 1}</span>
                        <span class="font-semibold text-gray-800">${intent.intent}</span>
                    </div>
                    <div class="text-right">
                        <span class="text-lg font-bold text-purple-600">${intent.count}</span>
                        <span class="text-sm text-gray-500 ml-2">(${percentage}%)</span>
                    </div>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded-full transition-all duration-500"
                         style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

function updateLogsTable() {
    const tbody = document.getElementById('logsTableBody');
    
    if (logsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-8 text-center text-gray-500">Tidak ada data</td></tr>';
        document.getElementById('logsCount').textContent = 'Menampilkan 0 percakapan';
        return;
    }

    tbody.innerHTML = logsData.map(log => {
        const date = new Date(log.timestamp);
        const confidenceColor = log.confidence > 0.8 ? 'text-green-600' : 
                               log.confidence > 0.5 ? 'text-yellow-600' : 'text-red-600';
        
        return `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-sm text-gray-600">
                    ${date.toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })} 
                    ${date.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}
                </td>
                <td class="px-4 py-3 text-sm text-gray-800 max-w-md truncate">${log.user_message}</td>
                <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded-full">
                        ${log.intent}
                    </span>
                </td>
                <td class="px-4 py-3 text-sm ${confidenceColor} font-medium">
                    ${Math.round((log.confidence || 0) * 100)}%
                </td>
                <td class="px-4 py-3 text-sm text-gray-600">
                    ${(log.response_time || 0).toFixed(3)}s
                </td>
            </tr>
        `;
    }).join('');

    document.getElementById('logsCount').textContent = `Menampilkan ${logsData.length} percakapan`;
}

function updateIntentFilter() {
    const select = document.getElementById('intentFilter');
    const intents = [...new Set(allLogs.map(log => log.intent))];
    
    select.innerHTML = '<option value="all">Semua Intent</option>' +
        intents.map(intent => `<option value="${intent}">${intent}</option>`).join('');
}

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
}

async function showAddIntentModal() {
    document.getElementById('modalTitle').textContent = 'Tambah Intent & Response Baru';
    document.getElementById('intentName').value = '';
    document.getElementById('intentPatterns').value = '';
    document.getElementById('intentResponseKey').value = '';
    document.getElementById('intentResponseText').value = '';
    document.getElementById('intentEntities').value = '';
    document.getElementById('intentQuickReplies').value = '';
    document.getElementById('editingIntent').value = '';
    document.getElementById('intentModal').classList.add('active');
}

async function editIntent(intent) {
    document.getElementById('modalTitle').textContent = 'Edit Intent & Response';
    document.getElementById('intentName').value = intent.intent;
    document.getElementById('intentPatterns').value = intent.patterns.join('\n');
    document.getElementById('intentResponseKey').value = intent.response_key;
    document.getElementById('intentEntities').value = (intent.entities || []).join(', ');
    document.getElementById('editingIntent').value = intent.intent;
    
    // Load response text
    try {
        const response = await fetch(`${API_URL}/admin/responses/${intent.response_key}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('intentResponseText').value = data.response.text || '';
            document.getElementById('intentQuickReplies').value = (data.response.quick_replies || []).join(', ');
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
    
    const intentName = document.getElementById('intentName').value.trim();
    const patterns = document.getElementById('intentPatterns').value.split('\n').map(p => p.trim()).filter(p => p);
    const responseKey = document.getElementById('intentResponseKey').value.trim();
    const responseText = document.getElementById('intentResponseText').value.trim();
    const entities = document.getElementById('intentEntities').value.split(',').map(e => e.trim()).filter(e => e);
    const quickReplies = document.getElementById('intentQuickReplies').value.split(',').map(q => q.trim()).filter(q => q);
    const editing = document.getElementById('editingIntent').value;
    
    if (!intentName || patterns.length === 0 || !responseKey || !responseText) {
        alert('Semua field bertanda * harus diisi!');
        return;
    }
    
    const intentData = {
        intent: intentName,
        patterns: patterns,
        response_key: responseKey,
        entities: entities
    };
    
    const responseData = {
        text: responseText,
        quick_replies: quickReplies
    };
    
    try {
        // Save intent
        const intentUrl = editing ? `${API_URL}/admin/intents/${editing}` : `${API_URL}/admin/intents`;
        const intentMethod = editing ? 'PUT' : 'POST';
        
        const intentResponse = await fetch(intentUrl, {
            method: intentMethod,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(intentData)
        });
        
        if (!intentResponse.ok) {
            const error = await intentResponse.json();
            alert('Error menyimpan intent: ' + error.error);
            return;
        }
        
        // Save response
        const responseResponse = await fetch(`${API_URL}/admin/responses/${responseKey}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(responseData)
        });
        
        if (!responseResponse.ok) {
            const error = await responseResponse.json();
            alert('Error menyimpan response: ' + error.error);
            return;
        }
        
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
            const error = await response.json();
            alert('Gagal menghapus intent: ' + error.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function switchTab(tab) {
    ['overviewTab', 'logsTab', 'intentsTab', 'manageTab'].forEach(id => {
        document.getElementById(id).style.display = 'none';
    });
    ['tabOverview', 'tabLogs', 'tabIntents', 'tabManage'].forEach(id => {
        document.getElementById(id).className = 'py-4 px-2 border-b-2 font-medium text-sm transition-colors tab-inactive';
    });
    
    document.getElementById(tab + 'Tab').style.display = 'block';
    document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1)).className = 'py-4 px-2 border-b-2 font-medium text-sm transition-colors tab-active';
}

function filterLogs() {
    const searchQuery = document.getElementById('searchInput').value.toLowerCase();
    const intentFilter = document.getElementById('intentFilter').value;
    
    logsData = allLogs.filter(log => {
        const matchesSearch = log.user_message.toLowerCase().includes(searchQuery) ||
                             log.bot_response.toLowerCase().includes(searchQuery);
        const matchesIntent = intentFilter === 'all' || log.intent === intentFilter;
        return matchesSearch && matchesIntent;
    });
    
    updateLogsTable();
}

function refreshData() {
    loadDashboard();
    alert('Data berhasil direfresh! 🔄');
}