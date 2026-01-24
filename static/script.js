/* script.js - Cashflow Dashboard */
let lastData = null;
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth();
let skipPromptCheck = false;
let editingTransactionId = null;
let addingDate = null;
let expandedTransactionId = null;
let addingTemplate = {};

document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = `
        /* Sticky Headers */
        header { position: sticky; top: 0; z-index: 1001; background-color: #121212; padding: 15px 0; border-bottom: 1px solid #333; width: 100%; }
        .calendar-header { position: sticky; top: 86px; z-index: 1000; background-color: #121212; margin: 0; padding: 15px 0; border-bottom: 1px solid #333; width: 100%; }
        
        /* Container */
        .excel-container { width: 100%; margin: 0 auto; border: 1px solid #444; background: #1e1e1e; font-family: 'Segoe UI', 'Inter', sans-serif; }
        
        /* Essential Fix for Grid */
        #calendar-grid { display: block !important; width: 100% !important; grid-template-columns: none !important; }
        
        table.excel-table { width: 100%; border-collapse: collapse; font-size: 13px; }

        /* Columns */
        .col-w-desc { width: 30%; }
        .col-w-party { width: 20%; }
        .col-w-vs { width: 10%; }
        .col-w-status { width: 10%; }
        .col-w-amt { width: 12%; text-align: right; }
        .col-w-act { width: 5%; text-align: center; }

        /* Table Header */
        thead.main-header th {
            position: sticky; top: 155px; z-index: 900; background: #333; color: #ddd; padding: 10px 8px; text-align: left; border-bottom: 2px solid #555; font-weight: 600; box-shadow: 0 2px 2px -1px rgba(0,0,0,0.4);
        }

        /* Rows */
        tr.day-header-row td { background: #2d2d30; color: #ccc; padding: 8px 12px; font-weight: bold; border-top: 1px solid #555; font-size: 14px; }
        tr.day-header-row.is-weekend td { background: #383030; color: #a88; }
        tr.day-header-row.is-today td { background: #FFF8E1; color: #000; border-bottom: 2px solid #FFD54F; }

        tr.tx-row td { padding: 6px 8px; border-bottom: 1px solid #2a2a2a; border-right: 1px solid #2a2a2a; color: #e0e0e0; vertical-align: middle; }
        tr.tx-row:hover { background: #2a2d3e; }

        tr.day-summary-row td { background: #252526; text-align: right; padding: 8px 15px; font-weight: bold; border-bottom: 2px solid #444; color: #fff; }

        /* Utilities */
        .text-income { color: #69f0ae; font-weight: 600; }
        .text-expense { color: #ff5252; font-weight: 600; }
        .text-income { color: #69f0ae; }
        .text-expense { color: #ff5252; }
        
        tr.tx-row.type-income { background: rgba(105, 240, 174, 0.05); }
        tr.tx-row.type-expense { background: rgba(255, 82, 82, 0.05); }
        tr.tx-row.type-income:hover { background: rgba(105, 240, 174, 0.1) !important; }
        tr.tx-row.type-expense:hover { background: rgba(255, 82, 82, 0.1) !important; }

        .text-muted { color: #777; font-size: 11px; }
        .badge-status { padding: 4px 8px; border-radius: 4px; font-size: 11px; text-transform: uppercase; font-weight: bold; }
        .badge-status.zaplaceno { background: #1b5e20; color: #a5d6a7; }
        .badge-status.nezaplaceno { background: #b71c1c; color: #ffcdd2; }
        input.edit-input, select.edit-input { background: #111; border: 1px solid #555; color: white; padding: 4px; border-radius: 3px; width: 100%; box-sizing: border-box; }

        /* Search Modal */
        .search-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 2000; justify-content: center; align-items: center; }
        .search-box { background: #252526; padding: 20px; border: 1px solid #444; border-radius: 8px; display: flex; gap: 10px; width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
        .search-btn { padding: 8px 16px; background: #69f0ae; color: #000; font-weight: bold; border: none; border-radius: 4px; cursor: pointer; }
    `;
    document.head.appendChild(style);
    fetchData();
    document.getElementById('prev-month').addEventListener('click', () => changeMonth(-1));
    document.getElementById('next-month').addEventListener('click', () => changeMonth(1));
});

function changeMonth(delta) {
    currentMonth += delta;
    if (currentMonth < 0) { currentMonth = 11; currentYear--; }
    else if (currentMonth > 11) { currentMonth = 0; currentYear++; }
    fetchData(true);
}

async function fetchData(skipCheck = false) {
    skipPromptCheck = skipCheck;
    try {
        const response = await fetch('/api/calendar_data');
        const data = await response.json();
        lastData = data;
        const balEl = document.getElementById('display-initial-balance');
        if (balEl) balEl.textContent = formatMoney(data.initial_balance);
        const currBalEl = document.getElementById('display-current-balance');
        if (currBalEl && data.current_total_balance !== undefined) {
            const bal = data.current_total_balance;
            currBalEl.textContent = formatMoney(bal);
            currBalEl.style.color = bal >= 0 ? '#69f0ae' : '#ff5252';
        }
        renderExcelView();
        if (!skipPromptCheck) checkStartupPrompt();
        const monthNames = ['Leden', 'Únor', 'Březen', 'Duben', 'Květen', 'Červen', 'Červenec', 'Srpen', 'Září', 'Říjen', 'Listopad', 'Prosinec'];
        document.getElementById('current-month-label').textContent = `${monthNames[currentMonth]} ${currentYear}`;
    } catch (error) { console.error('Error fetching data:', error); }
}

function renderExcelView() {
    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = '';
    const container = document.createElement('div');
    container.style.cssText = 'overflow-x: auto; padding: 20px;';

    const table = document.createElement('table');
    table.className = 'excel-table';
    table.style.cssText = 'width: 100%; border-collapse: collapse;';

    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr style="background: #2d2d30; border-bottom: 2px solid #555;">
            <th style="padding: 12px; text-align: left; color: #fff; font-weight: bold;">Datum</th>
            <th style="padding: 12px; text-align: right; color: #69f0ae; font-weight: bold;">Příjmy (dané)</th>
            <th style="padding: 12px; text-align: right; color: #ff5252; font-weight: bold;">Výdaje (dané)</th>
            <th style="padding: 12px; text-align: right; color: #ccc; font-weight: bold;">Denní změna</th>
            <th style="padding: 12px; text-align: right; color: #fff; font-weight: bold;">Kumulovaný stav</th>
        </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    // Get all dates from daily_status
    if (!lastData || !lastData.daily_status) {
        tbody.innerHTML = '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #777;">Žádná data</td></tr>';
        table.appendChild(tbody);
        container.appendChild(table);
        grid.appendChild(container);
        return;
    }

    const dailyStatus = lastData.daily_status;
    const sortedDates = Object.keys(dailyStatus).sort();

    sortedDates.forEach(dateStr => {
        const dayData = dailyStatus[dateStr];
        const income = dayData.income || 0;
        const expense = dayData.expense || 0;
        const dailyChange = income - expense;
        const balance = dayData.balance || 0;

        // Show only days with EXPENSES (received invoices)
        if (expense === 0) return;

        const tr = document.createElement('tr');
        tr.style.cssText = 'border-bottom: 1px solid #333; transition: background 0.2s; cursor: pointer;';
        tr.onmouseenter = () => tr.style.background = '#2a2a2a';
        tr.onmouseleave = () => tr.style.background = 'transparent';
        tr.onclick = () => {
            // Build invoice list
            let invoiceList = '';
            if (dayData.transactions && dayData.transactions.length > 0) {
                invoiceList = '\n\n📋 Faktúry splatné v tento deň:\n';
                dayData.transactions.forEach(t => {
                    const party = t.customer || t.supplier || 'Neznámy';
                    const vs = t.var_symbol || '-';
                    const type = t.amount >= 0 ? '📈 Príjem' : '📉 Výdaj';
                    invoiceList += `\n${type}: ${party}\nVS: ${vs}\nSuma: ${formatMoney(t.amount)}\n`;
                });
            }

            alert(`📊 Zostatok k ${dateStr.split('-').reverse().join('.')}:\n\nPríjmy: ${formatMoney(income)}\nVýdaje: ${formatMoney(expense)}\nZmena: ${formatMoney(dailyChange)}\n\n💰 Kumulovaný stav: ${formatMoney(balance)}${invoiceList}`);
        };

        const balanceColor = balance >= 0 ? '#69f0ae' : '#ff5252';
        const changeColor = dailyChange >= 0 ? '#69f0ae' : '#ff5252';

        tr.innerHTML = `
            <td style="padding: 10px; color: #ccc;">${dateStr.split('-').reverse().join('.')}</td>
            <td style="padding: 10px; text-align: right; color: #69f0ae; font-weight: ${income > 0 ? 'bold' : 'normal'};">${income > 0 ? formatMoney(income) : '0 Kč'}</td>
            <td style="padding: 10px; text-align: right; color: #ff5252; font-weight: ${expense > 0 ? 'bold' : 'normal'};">${expense > 0 ? formatMoney(expense) : '0 Kč'}</td>
            <td style="padding: 10px; text-align: right; color: ${changeColor};">${formatMoney(dailyChange)}</td>
            <td style="padding: 10px; text-align: right; color: ${balanceColor}; font-weight: bold; font-size: 15px;">${formatMoney(balance)}</td>
        `;

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
    grid.appendChild(container);
}

// Enhanced Add Row with Templates
window.showAddRow = (dateStr) => {
    let m = document.getElementById('tx-type-modal');
    if (!m) createTxTypeModal();
    m = document.getElementById('tx-type-modal');
    m.dataset.date = dateStr;
    m.style.display = 'flex';
};

window.createTxTypeModal = () => {
    const div = document.createElement('div');
    div.id = 'tx-type-modal';
    div.style.cssText = 'display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:2000; justify-content:center; align-items:center; backdrop-filter:blur(5px);';
    div.innerHTML = `
        <div style="background:#1e1e1e; padding:25px; border-radius:12px; border:1px solid #444; width:300px; text-align:center; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
            <h3 style="margin-top:0; color:#fff; margin-bottom:20px;">Vyberte typ transakce</h3>
            <button onclick="selectTxType('prijata')" style="display:block; width:100%; padding:10px; margin:5px 0; background:#333; border:none; color:white; cursor:pointer; border-radius:6px; text-align:left; padding-left:15px;">� Prijatá faktúra (Výdaj)</button>
            <button onclick="selectTxType('vystavena')" style="display:block; width:100%; padding:10px; margin:5px 0; background:#333; border:none; color:white; cursor:pointer; border-radius:6px; text-align:left; padding-left:15px;">� Vystavená faktúra (Príjem)</button>
            <button onclick="selectTxType('prijata_archiv')" style="display:block; width:100%; padding:10px; margin:5px 0; background:#333; border:none; color:#aaa; cursor:pointer; border-radius:6px; text-align:left; padding-left:15px;">🗄️ Prijatá archívna (Informativ)</button>
            <button onclick="selectTxType('vystavena_archiv')" style="display:block; width:100%; padding:10px; margin:5px 0; background:#333; border:none; color:#aaa; cursor:pointer; border-radius:6px; text-align:left; padding-left:15px;">🗄️ Vystavená archívna (Informativ)</button>
            <div style="height:1px; background:#444; margin:10px 0;"></div>
            <button onclick="selectTxType('vklad')" style="display:block; width:100%; padding:10px; margin:5px 0; background:#333; border:none; color:white; cursor:pointer; border-radius:6px; text-align:left; padding-left:15px;">💰 Extra vklad</button>
            <button onclick="selectTxType('ine')" style="display:block; width:100%; padding:10px; margin:5px 0; background:#333; border:none; color:white; cursor:pointer; border-radius:6px; text-align:left; padding-left:15px;">✏️ Jiné</button>
            <button onclick="document.getElementById('tx-type-modal').style.display='none'" style="margin-top:15px; background:transparent; border:none; color:#aaa; cursor:pointer; font-size:13px;">Zrušit</button>
        </div>
    `;
    document.body.appendChild(div);
}

window.selectTxType = (type) => {
    const m = document.getElementById('tx-type-modal');
    const dateStr = m.dataset.date;
    m.style.display = 'none';

    addingTemplate = { type: type };
    if (type === 'vklad') { addingTemplate = { ...addingTemplate, party: 'Vlastní vklad', desc: 'Extra vklad' }; }
    if (type === 'pohledavka') { addingTemplate = { ...addingTemplate, desc: 'Splacená pohledávka' }; }
    if (type === 'prijata_archiv' || type === 'vystavena_archiv') { addingTemplate.status = 'archiv'; }

    addingDate = dateStr;
    renderExcelView();
};

window.cancelAdd = () => { addingDate = null; renderExcelView(); };
window.saveNewTransaction = async (dateStr) => {
    const finalDate = document.getElementById('new-date').value || dateStr;
    const vs = document.getElementById('new-vs').value;
    const party = document.getElementById('new-party').value;
    const amt = document.getElementById('new-amt').value;
    const desc = document.getElementById('new-desc').value;
    const status = document.getElementById('new-status').value;
    let finalAmt = parseFloat(amt);
    let type = 'Výdaj';

    // Auto-detect type and sign based on Template selection
    if (addingTemplate.type) {
        if (addingTemplate.type.includes('prijata')) {
            finalAmt = -Math.abs(finalAmt); // Always negative for Expense
            type = 'Výdaj';
        } else if (addingTemplate.type.includes('vystavena') || addingTemplate.type === 'vklad' || addingTemplate.type === 'pohledavka') {
            finalAmt = Math.abs(finalAmt); // Always positive for Income
            type = 'Příjem';
        }
    } else {
        // Fallback if no template (e.g. direct add?)
        if (finalAmt > 0) type = 'Příjem';
    }

    const payload = { date: finalDate, amount: finalAmt, description: desc, supplier: party, var_symbol: vs, payment_status: status, type: type };
    try {
        const res = await fetch('/api/add_transaction', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if ((await res.json()).status === 'success') { addingDate = null; fetchData(true); }
    } catch (e) { alert('Chyba: ' + e); }
}
window.startEdit = (id) => { editingTransactionId = id; renderExcelView(); }
window.cancelEdit = () => { editingTransactionId = null; renderExcelView(); }
window.saveTransaction = async (id) => {
    const date = document.getElementById(`ed-date-${id}`).value;
    const amt = document.getElementById(`ed-amt-${id}`).value;
    const desc = document.getElementById(`ed-desc-${id}`).value;
    const party = document.getElementById(`ed-party-${id}`).value;
    const vs = document.getElementById(`ed-vs-${id}`).value;
    const status = document.getElementById(`ed-status-${id}`).value;
    const payload = { id: id, date, amount: amt, description: desc, supplier: party, var_symbol: vs, payment_status: status };
    try {
        const res = await fetch('/api/update_transaction', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if ((await res.json()).status === 'success') { editingTransactionId = null; fetchData(true); }
    } catch (e) { alert('Chyba: ' + e); }
}
window.deleteTransaction = async (id) => {
    if (!confirm('Smazat?')) return;
    try {
        const res = await fetch('/api/delete_transaction', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) });
        if ((await res.json()).status === 'success') fetchData(true);
    } catch (e) { alert('Chyba: ' + e); }
}
window.toggleDetails = (id) => { expandedTransactionId = (expandedTransactionId === id) ? null : id; renderExcelView(); }

function formatMoney(amount) { return new Intl.NumberFormat('cs-CZ', { style: 'currency', currency: 'CZK', maximumFractionDigits: 0 }).format(amount); }
function getCzechHolidays(year) {
    const fixed = [{ d: '01-01', n: 'Nový rok' }, { d: '05-01', n: 'Svátek práce' }, { d: '05-08', n: 'Den vítězství' }, { d: '07-05', n: 'Cyril a Metoděj' }, { d: '07-06', n: 'Jan Hus' }, { d: '09-28', n: 'Den české státnosti' }, { d: '10-28', n: 'Vznik ČSR' }, { d: '11-17', n: 'Den boje za svobodu' }, { d: '12-24', n: 'Štědrý den' }, { d: '12-25', n: '1. sv. vánoční' }, { d: '12-26', n: '2. sv. vánoční' }];
    const a = year % 19, b = Math.floor(year / 100), c = year % 100, d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30, i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
    const mo = Math.floor((h + l - 7 * m + 114) / 31), dy = ((h + l - 7 * m + 114) % 31) + 1;
    const easter = new Date(year, mo - 1, dy);
    const fmt = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    const gf = new Date(easter); gf.setDate(easter.getDate() - 2);
    const em = new Date(easter); em.setDate(easter.getDate() + 1);
    return [...fixed.map(x => ({ date: `${year}-${x.d}`, name: x.n })), { date: fmt(gf), name: "Velký pátek" }, { date: fmt(em), name: "Velikonoční pondělí" }];
}
function checkStartupPrompt() { if (localStorage.getItem('hideStartupPrompt') === 'true') return; const m = document.getElementById('startup-prompt-modal'); if (m) m.style.display = 'flex'; }
function closeStartupPrompt() { document.getElementById('startup-prompt-modal').style.display = 'none'; }
async function saveStartupBalance() {
    const val = document.getElementById('startup-balance-input').value;
    const hide = document.getElementById('dont-show-startup-again').checked;
    if (hide) localStorage.setItem('hideStartupPrompt', 'true');
    await fetch('/api/initial_balance', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ amount: val }) });
    closeStartupPrompt();
    fetchData(true);
}
function resetStartupPrompt() { localStorage.removeItem('hideStartupPrompt'); alert('Uvítací okno bylo resetováno.'); }

/* Search Functions */
function openSearch() {
    let m = document.getElementById('search-modal');
    if (!m) {
        m = document.createElement('div');
        m.id = 'search-modal';
        m.className = 'search-modal';
        m.innerHTML = `
            <div class="search-box">
                <input id="search-input" class="edit-input" placeholder="Hledat (VS, Firma...)" autofocus style="font-size:16px; padding:8px;">
                <button class="search-btn" onclick="performSearch()">Hledat</button>
                <button onclick="document.getElementById('search-modal').style.display='none'" style="margin-left:auto; background:none; border:none; color:#777; cursor:pointer;">✕</button>
            </div>
        `;
        document.body.appendChild(m);
        m.querySelector('input').addEventListener('keypress', e => { if (e.key === 'Enter') performSearch(); });
    }
    m.style.display = 'flex';
    setTimeout(() => document.getElementById('search-input').focus(), 100);
}
async function performSearch() {
    const q = document.getElementById('search-input').value;
    if (!q) return;
    document.getElementById('search-modal').style.display = 'none';
    try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const results = await res.json();
        renderSearchResults(results, q);
    } catch (e) { alert('Chyba vyhledávání: ' + e); }
}
function renderSearchResults(results, query) {
    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = '';
    const container = document.createElement('div');
    container.className = 'excel-container';
    container.innerHTML = `
        <div style="padding:15px; background:#1e1e1e; border-bottom:1px solid #444; display:flex; justify-content:space-between; align-items:center; position:sticky; top:0; z-index:1001;">
            <h2 style="margin:0; font-size:18px; color:#ddd;">Výsledky hledání: "${query}" (${results.length})</h2>
            <button onclick="fetchData()" style="padding:6px 12px; background:#333; color:#fff; border:1px solid #555; cursor:pointer;">Zpět na kalendář</button>
        </div>
        <table class="excel-table">
            <thead class="main-header">
                <tr>
                    <th style="width:12%">Datum</th>
                    <th class="col-w-vs">VS</th>
                    <th class="col-w-party">Firma</th>
                    <th class="col-w-amt">Částka</th>
                    <th class="col-w-status">Stav</th>
                    <th>Popis</th>
                </tr>
            </thead>
            <tbody>
                ${results.map(t => {
        const amtClass = t.amount >= 0 ? 'text-income' : 'text-expense';
        const party = t.customer || t.supplier || '';
        return `<tr class="tx-row"><td>${t.date}</td><td style="font-family:monospace; color:#ccc">${t.var_symbol || ''}</td><td style="font-weight:600">${party}</td><td class="${amtClass}" style="text-align:right">${formatMoney(t.amount)}</td><td><span class="badge-status ${t.payment_status?.toLowerCase()}">${t.payment_status || '-'}</span></td><td>${t.description || t.text || ''}</td></tr>`;
    }).join('')}
            </tbody>
        </table>
    `;
    grid.appendChild(container);
}

/* Settings Logic */
function openSettingsModal() {
    const m = document.getElementById('settings-modal');
    if (m) m.style.display = 'flex';
    loadBackupList();
}
function closeSettingsModal() { document.getElementById('settings-modal').style.display = 'none'; }
function logout() { window.location.href = '/logout'; }
async function createBackup() {
    try {
        const res = await fetch('/api/backup/create', { method: 'POST' });
        const d = await res.json();
        if (d.status === 'success') { alert(d.message); loadBackupList(); }
        else alert(d.message);
    } catch (e) { alert('Chyba: ' + e); }
}
async function loadBackupList() {
    try {
        const res = await fetch('/api/backup/list');
        const d = await res.json();
        const list = document.getElementById('backup-list');
        if (list) {
            // Make list scrollable
            list.style.maxHeight = '300px';
            list.style.overflowY = 'auto';
            list.style.border = '1px solid #444';
            list.style.borderRadius = '4px';
            list.style.padding = '5px';
            list.style.background = '#1e1e1e';

            if (d.backups && d.backups.length > 0) {
                list.innerHTML = d.backups.map(b => `
                    <div style="display:flex; justify-content:space-between; padding:10px; border-bottom:1px solid #333; align-items:center; flex-wrap: wrap; gap: 10px;">
                        <span style="color:#ddd; font-family:monospace; margin-right: 10px;">
                            ${b.filename} <br><span style="color:#777; font-size:11px">(${b.size}, ${b.created})</span>
                        </span>
                        <div style="display: flex; gap: 8px; flex-shrink: 0;">
                            <button onclick="restoreBackupFromList('${b.filename}')" style="background:#444; color:#fff; border:none; padding:6px 12px; cursor:pointer; border-radius:4px; font-size: 13px; white-space: nowrap;">↻ Obnovit</button>
                            <a href="/api/backup/download/${b.filename}" target="_blank" style="color:#69f0ae; text-decoration:none; padding:6px 12px; border:1px solid #69f0ae; border-radius:4px; font-size:13px; white-space: nowrap; display: inline-block;">⬇ Stáhnout</a>
                        </div>
                    </div>
                `).join('');
            } else {
                list.innerHTML = '<p style="color:#777; text-align:center; padding:10px;">Žadné zálohy</p>';
            }
        }
    } catch (e) { console.error(e); }
}
async function restoreBackupFromList(filename) {
    if (!confirm('Opravdu obnovit? Data budou přepsána!')) return;
    try {
        const res = await fetch('/api/backup/restore', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ filename }) });
        const d = await res.json();
        if (d.status === 'success') {
            alert('✅ Obnoveno úspěšně. Stránka se obnoví...');
            location.reload();
        }
        else alert('❌ Chyba: ' + d.message);
    } catch (e) { alert('Chyba komunikace: ' + e); }
}
async function restoreBackup() {
    const fileInput = document.getElementById('backup-file-input');
    if (!fileInput || !fileInput.files[0]) {
        alert("Vyberte prosím soubor zálohy.");
        return;
    }
    const file = fileInput.files[0];

    // Potvrzení
    if (!confirm(`Opravdu obnovit ze souboru '${file.name}'? Současná data budou přepsána.`)) return;

    const formData = new FormData();
    formData.append('file', file);

    // UI feedback
    const btn = document.querySelector('button[onclick="restoreBackup()"]');
    const originalText = btn ? btn.textContent : 'Nahrát a obnovit';
    if (btn) { btn.textContent = 'Obnovuji...'; btn.disabled = true; }

    try {
        const res = await fetch('/api/backup/restore', { method: 'POST', body: formData });
        const d = await res.json(); // Read JSON once

        if (d.status === 'success') {
            alert('✅ Obnoveno úspěšně. Stránka se obnoví...');
            location.reload();
        } else {
            alert('❌ Chyba obnovy: ' + (d.message || 'Neznámá chyba'));
            if (btn) { btn.textContent = originalText; btn.disabled = false; }
        }
    } catch (e) {
        alert('❌ Chyba komunikace: ' + e);
        if (btn) { btn.textContent = originalText; btn.disabled = false; }
    }
}

/* --- Added Section: Detailed Settings Logic --- */

/* Settings Navigation */
function showSettingsTab(tabId) {
    document.querySelectorAll('.settings-tab').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.settings-menu-item').forEach(el => el.classList.remove('active'));

    const tab = document.getElementById(`tab-${tabId}`);
    if (tab) tab.style.display = 'block';

    const menu = document.getElementById(`menu-${tabId}`);
    if (menu) menu.classList.add('active');

    if (tabId === 'users') loadUsers();
    if (tabId === 'files') loadUploadedFiles();
    if (tabId === 'backup') loadBackupList();
    if (tabId === 'logs') loadAuditLog();
    if (tabId === 'flexibee') loadFlexiBeeConfig();
}

/* User Management */
async function loadUsers() {
    try {
        const res = await fetch('/api/users');
        const data = await res.json();
        const list = document.getElementById('users-list');
        if (!list) return;
        list.innerHTML = '';

        if (data.users) {
            data.users.forEach(u => {
                const el = document.createElement('div');
                el.style.background = 'rgba(118, 118, 128, 0.12)';
                el.style.padding = '15px';
                el.style.marginBottom = '10px';
                el.style.borderRadius = '8px';
                el.style.display = 'flex';
                el.style.justifyContent = 'space-between';
                el.style.alignItems = 'center';
                el.innerHTML = `
                    <div>
                        <div style="font-weight:bold; color:#fff">${u.username} <span style="font-size:11px; color:#aaa; font-weight:normal">(${u.role})</span></div>
                        <div style="color:#777; font-size:12px">${u.name || ''}</div>
                    </div>
                    ${u.username !== 'admin' ? `<button onclick="deleteUser('${u.username}')" style="background:#b71c1c; border:none; color:white; padding:5px 10px; border-radius:4px; cursor:pointer;">Smazat</button>` : ''}
                `;
                list.appendChild(el);
            });
        }
    } catch (e) { console.error(e); }
}

function showAddUserForm() { document.getElementById('add-user-form').style.display = 'block'; }
function hideAddUserForm() { document.getElementById('add-user-form').style.display = 'none'; }

async function createUser() {
    const username = document.getElementById('new-username').value;
    const name = document.getElementById('new-name').value;
    const password = document.getElementById('new-password').value;
    const role = document.getElementById('new-role').value;

    try {
        const res = await fetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, name, password, role })
        });
        const d = await res.json();
        if (d.status === 'success') {
            alert('Uživatel vytvořen');
            hideAddUserForm();
            loadUsers();
            document.getElementById('new-username').value = '';
            document.getElementById('new-name').value = '';
            document.getElementById('new-password').value = '';
        } else alert(d.message);
    } catch (e) { alert(e); }
}

async function deleteUser(username) {
    if (!confirm(`Opravdu smazat uživatele ${username}?`)) return;
    try {
        const res = await fetch(`/api/users/${username}`, { method: 'DELETE' });
        const d = await res.json();
        if (d.status === 'success') loadUsers();
        else alert(d.message);
    } catch (e) { alert(e); }
}

/* File Import & Management */
async function loadUploadedFiles() {
    try {
        const resReceived = await fetch('/api/files/prijate');
        const dataReceived = await resReceived.json();
        renderFileList('files-prijate-list', dataReceived.files || [], 'prijate');

        const resIssued = await fetch('/api/files/vydane');
        const dataIssued = await resIssued.json();
        renderFileList('files-vydane-list', dataIssued.files || [], 'vydane');
    } catch (e) { console.error(e); }
}

function renderFileList(elementId, files, type) {
    const list = document.getElementById(elementId);
    if (!list) return;
    if (!files.length) { list.innerHTML = '<p style="color:#777">Žádné soubory</p>'; return; }
    list.innerHTML = files.map(f => `
        <div style="display:flex; justify-content:space-between; margin-bottom:5px; border-bottom:1px solid #444; padding-bottom:5px;">
            <span style="color:#ddd; font-size:13px;">${f}</span>
            <button onclick="deleteFile('${f}', '${type}')" style="color:#ff5252; background:none; border:none; cursor:pointer;">✕</button>
        </div>
    `).join('');
}

async function deleteFile(filename, type) {
    if (!confirm('Smazat soubor?')) return;
    try {
        await fetch('/api/delete_file', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename, type })
        });
        loadUploadedFiles();
    } catch (e) { alert(e); }
}

async function handleFileUpload(input, type) {
    if (!input.files[0]) return;
    const formData = new FormData();
    formData.append(type, input.files[0]);

    try {
        const res = await fetch('/api/upload_csv', { method: 'POST', body: formData });
        let d;
        try { d = await res.json(); } catch (err) { throw new Error('Server returned invalid JSON'); }

        if (d.status === 'success') {
            alert(d.message);
            loadUploadedFiles();
        } else {
            alert('Chyba: ' + (d.message || 'Neznámá chyba'));
        }
    } catch (e) { alert('Chyba nahrávání: ' + e); }
    input.value = '';
}

/* Audit Log */
async function loadAuditLog() {
    try {
        const res = await fetch('/api/audit_log');
        const logs = await res.json();
        const list = document.getElementById('audit-log-list');
        if (!list) return;
        list.innerHTML = logs.map(l => `
            <tr style="border-bottom:1px solid #333;">
                <td style="padding:8px; color:#aaa;">${l.timestamp}</td>
                <td style="padding:8px; color:#fff;">${l.user}</td>
                <td style="padding:8px; color:#69f0ae;">${l.action}</td>
                <td style="padding:8px; color:#aaa; font-family:monospace; font-size:11px;">${JSON.stringify(l.details || {})}</td>
            </tr>
        `).join('');
    } catch (e) { }
}

/* Aliases and Helpers */
window.loadBackups = loadBackupList;
window.uploadBackup = restoreBackup;
window.saveBackupConfig = async () => {
    const enabled = document.getElementById('backup-enabled').checked;
    const interval = document.getElementById('backup-interval').value;
    const max = document.getElementById('backup-max').value;
    try {
        await fetch('/api/backup/config', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auto_backup: enabled, interval_hours: parseInt(interval), max_backups: parseInt(max) })
        });
        alert('Uloženo');
    } catch (e) { alert(e); }
}
window.confirmResetDB = async () => {
    if (confirm('OPRAVDU SMAZAT VŠECHNO?')) {
        await fetch('/api/reset_db', { method: 'POST' });
        location.reload();
    }
}
window.confirmRestartServer = async () => {
    if (confirm('Restartovat server?')) {
        await fetch('/api/restart_server', { method: 'POST' });
        alert('Server se restartuje...');
        setTimeout(() => location.reload(), 3000);
    }
}
window.updateInitialBalanceFromSettings = async () => {
    const val = document.getElementById('settings-initial-balance').value;
    await fetch('/api/initial_balance', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ amount: val }) });
    alert('Uloženo');
    fetchData();
}


// Initial binding of change password is tricky without UI events, but UI calls changePassword() directly.
// We need to implement changePassword if used.
window.changePassword = async () => {
    // Basic stub without backend endpoint verification in this turn
    alert('Změna hesla zatím není plně implementována (vyžaduje API endpoint).');
}

// Invoice Modal Functions
window.openInvoiceModal = (type) => {
    const modal = document.getElementById('invoice-modal');
    const title = document.getElementById('invoice-modal-title');
    const content = document.getElementById('invoice-modal-content');

    title.textContent = type === 'prijate' ? '📥 Prijaté faktúry (Výdaje)' : '📤 Vystavené faktúry (Príjmy)';

    // Filter transactions by type (store globally for edit modal)
    window.allTransactions = [];
    if (lastData && lastData.daily_status) {
        Object.values(lastData.daily_status).forEach(day => {
            if (day.transactions) {
                day.transactions.forEach(t => {
                    const isExpense = t.amount < 0;
                    const isIncome = t.amount > 0;
                    if ((type === 'prijate' && isExpense) || (type === 'vystavene' && isIncome)) {
                        window.allTransactions.push(t);
                    }
                });
            }
        });
    }

    // Sort by date
    window.allTransactions.sort((a, b) => new Date(a.date) - new Date(b.date));

    // Render table
    let html = '';

    // Add button for both types
    if (type === 'vystavene') {
        html += `
            <div style="margin-bottom: 15px; text-align: right;">
                <button onclick="showAddIncomeForm()" style="background: #69f0ae; color: #000; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px;">
                    ➕ Pridať príjem
                </button>
            </div>
        `;
    } else if (type === 'prijate') {
        html += `
            <div style="margin-bottom: 15px; text-align: right;">
                <button onclick="showAddExpenseForm()" style="background: #ff5252; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px;">
                    ➕ Pridať výdaj
                </button>
            </div>
        `;
    }

    html += `
        <div style="width: 100%; max-height: 600px; overflow-y: auto; border: 1px solid #333; border-radius: 8px;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead style="position: sticky; top: 0; background: #2d2d30; border-bottom: 2px solid #555; z-index: 10;">
                    <tr>
                        <th style="padding: 12px; text-align: left;">Dátum splatnosti</th>
                        <th style="padding: 12px; text-align: left;">VS</th>
                        <th style="padding: 12px; text-align: left;">Firma</th>
                        <th style="padding: 12px; text-align: right;">Suma</th>
                        <th style="padding: 12px; text-align: left;">Popis</th>
                        <th style="padding: 12px; text-align: center;">Akcie</th>
                    </tr>
                </thead>
                <tbody>
    `;


    window.allTransactions.forEach(t => {
        const party = t.customer || t.supplier || '';
        const desc = t.description || t.text || '';

        html += `
            <tr style="border-bottom: 1px solid #333;">
                <td style="padding: 10px;">${t.date ? t.date.split('-').reverse().join('.') : '-'}</td>
                <td style="padding: 10px; font-family: monospace;">${t.var_symbol || ''}</td>
                <td style="padding: 10px;">${party}</td>
                <td style="padding: 10px; text-align: right; color: ${t.amount >= 0 ? '#69f0ae' : '#ff5252'}; font-weight: bold;">${formatMoney(t.amount)}</td>
                <td style="padding: 10px; color: #aaa;">${desc}</td>
                <td style="padding: 10px; text-align: center;">
                    <button onclick="startInvoiceEdit('${t.id}')" style="background: #555; border: none; color: white; padding: 5px 10px; border-radius: 4px; cursor: pointer; margin-right: 5px;">✏️ Upravit</button>
                    <button onclick="deleteTransaction('${t.id}')" style="background: #b71c1c; border: none; color: white; padding: 5px 10px; border-radius: 4px; cursor: pointer;">🗑️</button>
                </td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
        </div>
    `;

    content.innerHTML = html;
    modal.style.display = 'flex';

    // Store current type for edit functions
    window.currentInvoiceType = type;
};

window.closeInvoiceModal = () => {
    document.getElementById('invoice-modal').style.display = 'none';
    fetchData(true); // Refresh main view
};

window.startInvoiceEdit = (id) => {
    // Find the transaction
    const transaction = window.allTransactions.find(t => t.id === id);
    if (!transaction) {
        alert('Faktúra nenájdená');
        return;
    }

    // Store the ID for saving
    window.editingInvoiceId = id;

    // Populate modal fields
    document.getElementById('edit-invoice-date').value = transaction.date || '';
    document.getElementById('edit-invoice-vs').value = transaction.var_symbol || '';
    document.getElementById('edit-invoice-party').value = transaction.customer || transaction.supplier || '';
    document.getElementById('edit-invoice-amount').value = formatMoney(transaction.amount);
    document.getElementById('edit-invoice-desc').value = transaction.description || transaction.text || '';

    // Show modal
    document.getElementById('edit-invoice-modal').style.display = 'flex';
};

window.closeEditInvoiceModal = () => {
    window.editingInvoiceId = null;
    document.getElementById('edit-invoice-modal').style.display = 'none';
};

window.saveEditedInvoice = async () => {
    const id = window.editingInvoiceId;
    if (!id) return;

    const newDate = document.getElementById('edit-invoice-date').value;

    try {
        const res = await fetch('/api/update_transaction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: id,
                date: newDate
            })
        });

        const result = await res.json();
        if (result.status === 'success') {
            // Close modal
            closeEditInvoiceModal();

            // Refresh data in background
            await fetchData(true);

            // Re-render the invoice list WITHOUT scrolling to top
            openInvoiceModal(window.currentInvoiceType);

            // Show success message
            alert('✅ Faktúra úspešne upravená');
        } else {
            alert('❌ Chyba: ' + (result.message || 'Neznáma chyba'));
        }
    } catch (e) {
        alert('❌ Chyba: ' + e);
    }
};

// Remove old cancelInvoiceEdit function (no longer needed)

// Add Income Form Functions
window.showAddIncomeForm = () => {
    window.addingIncome = true;
    window.newIncomeType = null;

    // Show type selection
    const content = document.getElementById('invoice-modal-content');
    content.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <h3 style="margin-bottom: 30px; color: #fff;">Vyberte typ príjmu</h3>
            <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                <button onclick="selectIncomeType('vystavena')" style="background: rgba(105, 240, 174, 0.2); border: 2px solid #69f0ae; color: #69f0ae; padding: 20px 30px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; min-width: 200px;">
                    📄 Vystavená faktúra
                </button>
                <button onclick="selectIncomeType('vklad')" style="background: rgba(105, 240, 174, 0.2); border: 2px solid #69f0ae; color: #69f0ae; padding: 20px 30px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; min-width: 200px;">
                    💰 Vklad
                </button>
                <button onclick="selectIncomeType('ine')" style="background: rgba(105, 240, 174, 0.2); border: 2px solid #69f0ae; color: #69f0ae; padding: 20px 30px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; min-width: 200px;">
                    ✏️ Iné
                </button>
            </div>
            <div style="margin-top: 30px;">
                <button onclick="cancelAddIncome()" style="background: #555; border: none; color: white; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
                    Zrušiť
                </button>
            </div>
        </div>
    `;
};

window.selectIncomeType = (type) => {
    window.newIncomeType = type;
    const content = document.getElementById('invoice-modal-content');

    const today = new Date().toISOString().split('T')[0];
    const isVklad = type === 'vklad';

    content.innerHTML = `
        <div style="background: #2a2a2a; padding: 30px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
            <h3 style="margin-top: 0; color: #69f0ae; margin-bottom: 25px;">
                ${type === 'vystavena' ? '📄 Nová vystavená faktúra' : type === 'vklad' ? '💰 Nový vklad' : '✏️ Iný príjem'}
            </h3>
            
            <div style="display: grid; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">Dátum splatnosti *</label>
                    <input type="date" id="new-income-date" value="${today}" style="width: 100%; background: #111; border: 1px solid #555; color: white; padding: 10px; border-radius: 4px;">
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">Variabilný symbol</label>
                    <input type="text" id="new-income-vs" placeholder="VS" style="width: 100%; background: #111; border: 1px solid #555; color: white; padding: 10px; border-radius: 4px;">
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">${isVklad ? 'Zdroj' : 'Zákazník'}</label>
                    <input type="text" id="new-income-party" placeholder="${isVklad ? 'Vlastný vklad' : 'Názov firmy'}" value="${isVklad ? 'Vlastný vklad' : ''}" ${isVklad ? 'readonly style="color: #aaa;"' : ''} style="width: 100%; background: #111; border: 1px solid #555; color: white; padding: 10px; border-radius: 4px;">
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">Suma (Kč) *</label>
                    <input type="number" id="new-income-amount" placeholder="0" style="width: 100%; background: #111; border: 1px solid #69f0ae; color: #69f0ae; padding: 10px; border-radius: 4px; font-weight: bold; font-size: 16px;">
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">Popis</label>
                    <input type="text" id="new-income-desc" placeholder="${isVklad ? 'Extra vklad' : 'Popis transakcie'}" value="${isVklad ? 'Extra vklad' : ''}" style="width: 100%; background: #111; border: 1px solid #555; color: white; padding: 10px; border-radius: 4px;">
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 25px;">
                <button onclick="cancelAddIncome()" style="background: #555; border: none; color: white; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
                    Zrušiť
                </button>
                <button onclick="saveNewIncome()" style="background: #69f0ae; color: #000; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                    💾 Uložiť
                </button>
            </div>
        </div>
    `;
};

window.cancelAddIncome = () => {
    window.addingIncome = false;
    window.newIncomeType = null;
    openInvoiceModal('vystavene');
};

window.saveNewIncome = async () => {
    const date = document.getElementById('new-income-date').value;
    const vs = document.getElementById('new-income-vs').value;
    const party = document.getElementById('new-income-party').value;
    const amount = parseFloat(document.getElementById('new-income-amount').value);
    const desc = document.getElementById('new-income-desc').value;

    if (!date || !amount || amount <= 0) {
        alert('Vyplňte dátum a sumu!');
        return;
    }

    try {
        const res = await fetch('/api/add_transaction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: date,
                amount: Math.abs(amount), // Always positive for income
                description: desc,
                supplier: '',
                customer: party,
                var_symbol: vs,
                payment_status: 'zaplaceno',
                type: 'Příjem'
            })
        });

        if ((await res.json()).status === 'success') {
            window.addingIncome = false;
            window.newIncomeType = null;
            await fetchData(true);
            openInvoiceModal('vystavene');
        }
    } catch (e) {
        alert('Chyba: ' + e);
    }
};

// Overview Modal - Complete transaction list
window.openOverviewModal = () => {
    const modal = document.getElementById('invoice-modal');
    const title = document.getElementById('invoice-modal-title');
    const content = document.getElementById('invoice-modal-content');

    title.textContent = '📊 Kompletný prehľad (Príjmy + Výdaje)';

    // Get all dates from daily_status
    if (!lastData || !lastData.daily_status) {
        content.innerHTML = '<p style="padding: 20px; text-align: center; color: #777;">Žiadne dáta</p>';
        modal.style.display = 'flex';
        return;
    }

    const dailyStatus = lastData.daily_status;
    const sortedDates = Object.keys(dailyStatus).sort();

    let html = `
        <table style="width: 100%; border-collapse: collapse;">
            <thead style="background: #2d2d30; border-bottom: 2px solid #555;">
                <tr>
                    <th style="padding: 12px; text-align: left;">Dátum</th>
                    <th style="padding: 12px; text-align: right; color: #69f0ae;">Príjmy (dané)</th>
                    <th style="padding: 12px; text-align: right; color: #ff5252;">Výdaje (dané)</th>
                    <th style="padding: 12px; text-align: right; color: #ccc;">Denná zmena</th>
                    <th style="padding: 12px; text-align: right; color: #fff;">Kumulovaný stav</th>
                </tr>
            </thead>
            <tbody>
    `;

    sortedDates.forEach(dateStr => {
        const dayData = dailyStatus[dateStr];
        const income = dayData.income || 0;
        const expense = dayData.expense || 0;
        const dailyChange = income - expense;
        const balance = dayData.balance || 0;

        // Show all days with activity
        if (income === 0 && expense === 0) return;

        const balanceColor = balance >= 0 ? '#69f0ae' : '#ff5252';
        const changeColor = dailyChange >= 0 ? '#69f0ae' : '#ff5252';

        html += `
            <tr style="border-bottom: 1px solid #333;">
                <td style="padding: 10px; color: #ccc;">${dateStr.split('-').reverse().join('.')}</td>
                <td style="padding: 10px; text-align: right; color: #69f0ae; font-weight: ${income > 0 ? 'bold' : 'normal'};">${income > 0 ? formatMoney(income) : '0 Kč'}</td>
                <td style="padding: 10px; text-align: right; color: #ff5252; font-weight: ${expense > 0 ? 'bold' : 'normal'};">${expense > 0 ? formatMoney(expense) : '0 Kč'}</td>
                <td style="padding: 10px; text-align: right; color: ${changeColor};">${formatMoney(dailyChange)}</td>
                <td style="padding: 10px; text-align: right; color: ${balanceColor}; font-weight: bold; font-size: 15px;">${formatMoney(balance)}</td>
            </tr>
        `;
    });

    html += `
            </tbody>
        </table>
    `;

    content.innerHTML = html;
    modal.style.display = 'flex';
};

// Add Expense Form Functions
window.showAddExpenseForm = () => {
    const content = document.getElementById('invoice-modal-content');
    const today = new Date().toISOString().split('T')[0];

    content.innerHTML = `
        <div style="background: #2a2a2a; padding: 30px; border-radius: 8px; max-width: 600px; margin: 0 auto;">
            <h3 style="margin-top: 0; color: #ff5252; margin-bottom: 25px;">
                📥 Nová prijatá faktúra (Výdaj)
            </h3>
            
            <div style="display: grid; gap: 15px;">
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">Dátum splatnosti *</label>
                    <input type="date" id="new-expense-date" value="${today}" style="width: 100%; background: #111; border: 1px solid #555; color: white; padding: 10px; border-radius: 4px;">
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">Variabilný symbol</label>
                    <input type="text" id="new-expense-vs" placeholder="VS" style="width: 100%; background: #111; border: 1px solid #555; color: white; padding: 10px; border-radius: 4px;">
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">Dodávateľ *</label>
                    <input type="text" id="new-expense-party" placeholder="Názov firmy" style="width: 100%; background: #111; border: 1px solid #555; color: white; padding: 10px; border-radius: 4px;">
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">Suma (Kč) *</label>
                    <input type="number" id="new-expense-amount" placeholder="0" style="width: 100%; background: #111; border: 1px solid #ff5252; color: #ff5252; padding: 10px; border-radius: 4px; font-weight: bold; font-size: 16px;">
                </div>
                
                <div>
                    <label style="display: block; margin-bottom: 5px; color: #ccc; font-size: 13px;">Popis</label>
                    <input type="text" id="new-expense-desc" placeholder="Popis transakcie" style="width: 100%; background: #111; border: 1px solid #555; color: white; padding: 10px; border-radius: 4px;">
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 25px;">
                <button onclick="cancelAddExpense()" style="background: #555; border: none; color: white; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
                    Zrušiť
                </button>
                <button onclick="saveNewExpense()" style="background: #ff5252; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                    💾 Uložiť
                </button>
            </div>
        </div>
    `;
};

window.cancelAddExpense = () => {
    openInvoiceModal('prijate');
};

window.saveNewExpense = async () => {
    const date = document.getElementById('new-expense-date').value;
    const vs = document.getElementById('new-expense-vs').value;
    const party = document.getElementById('new-expense-party').value;
    const amount = parseFloat(document.getElementById('new-expense-amount').value);
    const desc = document.getElementById('new-expense-desc').value;

    if (!date || !amount || amount <= 0 || !party) {
        alert('Vyplňte dátum, dodávateľa a sumu!');
        return;
    }

    try {
        const res = await fetch('/api/add_transaction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: date,
                amount: -Math.abs(amount), // Always negative for expense
                description: desc,
                supplier: party,
                customer: '',
                var_symbol: vs,
                payment_status: 'nezaplaceno',
                type: 'Výdaj'
            })
        });

        if ((await res.json()).status === 'success') {
            await fetchData(true);
            openInvoiceModal('prijate');
        }
    } catch (e) {
        alert('Chyba: ' + e);
    }
};
