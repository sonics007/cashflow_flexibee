/* FlexiBee Integration Functions */

// Load FlexiBee configuration
async function loadFlexiBeeConfig() {
    try {
        const res = await fetch('/api/flexibee/config');
        const config = await res.json();

        // Populate form fields
        document.getElementById('fb-host').value = config.host || '';
        document.getElementById('fb-company').value = config.company || '';
        document.getElementById('fb-user').value = config.user || '';
        document.getElementById('fb-password').value = config.password || '';
        document.getElementById('fb-enabled').checked = config.enabled || false;
        document.getElementById('fb-import-from-date').value = config.import_from_date || '';

        // Update status badge
        updateFlexiBeeStatus(config.enabled);

        console.log('FlexiBee config loaded:', config);
    } catch (e) {
        console.error('Error loading FlexiBee config:', e);
        alert('Chyba načítání konfigurace: ' + e);
    }
}

// Save FlexiBee configuration
async function saveFlexiBeeConfig() {
    const config = {
        host: document.getElementById('fb-host').value.trim(),
        company: document.getElementById('fb-company').value.trim(),
        user: document.getElementById('fb-user').value.trim(),
        password: document.getElementById('fb-password').value,
        enabled: document.getElementById('fb-enabled').checked,
        import_from_date: document.getElementById('fb-import-from-date').value || ''
    };

    // Validation
    if (!config.host || !config.company || !config.user || !config.password) {
        alert('Vyplňte všechna pole!');
        return;
    }

    try {
        const res = await fetch('/api/flexibee/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        const data = await res.json();

        if (data.status === 'success') {
            alert('✅ Konfigurace uložena!');
            updateFlexiBeeStatus(config.enabled);
        } else {
            alert('❌ Chyba: ' + (data.message || 'Neznámá chyba'));
        }
    } catch (e) {
        console.error('Error saving FlexiBee config:', e);
        alert('Chyba ukládání: ' + e);
    }
}

// Test FlexiBee connection
async function testFlexiBeeConnection() {
    const config = {
        host: document.getElementById('fb-host').value.trim(),
        company: document.getElementById('fb-company').value.trim(),
        user: document.getElementById('fb-user').value.trim(),
        password: document.getElementById('fb-password').value
    };

    // Validation
    if (!config.host || !config.company || !config.user || !config.password) {
        alert('Vyplňte všechna pole před testováním!');
        return;
    }

    // Show loading state
    const btn = event.target;
    const originalText = btn.textContent;
    btn.textContent = '⏳ Testování...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/flexibee/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        const data = await res.json();

        if (data.status === 'success') {
            alert(`✅ Připojení úspěšné!\n\nServer: ${data.server || 'N/A'}\nVerze: ${data.version || 'N/A'}`);
        } else {
            alert(`❌ Připojení selhalo!\n\nChyba: ${data.message || 'Neznámá chyba'}`);
        }
    } catch (e) {
        console.error('Error testing FlexiBee connection:', e);
        alert('❌ Chyba testování: ' + e);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// Run FlexiBee synchronization
async function runFlexiBeeSync() {
    const btn = document.getElementById('fb-sync-btn');
    const log = document.getElementById('fb-sync-log');

    if (!btn || !log) return;

    // Show loading state
    const originalText = btn.textContent;
    btn.textContent = '⏳ Synchronizace...';
    btn.disabled = true;
    log.textContent = 'Spouštím synchronizaci...\n';

    try {
        // Send current import_from_date from UI with the sync request
        const importFromDate = document.getElementById('fb-import-from-date')?.value || '';

        const res = await fetch('/api/flexibee/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ import_from_date: importFromDate })
        });

        const data = await res.json();

        if (data.status === 'success') {
            const details = data.details || {};
            log.textContent += `✅ Synchronizace dokončena!\n`;
            log.textContent += `Vydané faktury: ${details.invoices_issued || 0}\n`;
            log.textContent += `Přijaté faktury: ${details.invoices_received || 0}\n`;
            log.textContent += `Celkem: ${details.total_synced || 0}\n`;

            alert('✅ Synchronizace dokončena!');

            // Refresh calendar data
            if (typeof fetchData === 'function') {
                fetchData(true);
            }
        } else {
            log.textContent += `❌ Chyba: ${data.message || 'Neznámá chyba'}\n`;
            alert('❌ Synchronizace selhala: ' + (data.message || 'Neznámá chyba'));
        }
    } catch (e) {
        console.error('Error running FlexiBee sync:', e);
        log.textContent += `❌ Chyba: ${e}\n`;
        alert('❌ Chyba synchronizace: ' + e);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// Update FlexiBee status badge
function updateFlexiBeeStatus(enabled) {
    const statusEl = document.getElementById('flexibee-status');
    if (!statusEl) return;

    if (enabled) {
        statusEl.textContent = 'Aktivní';
        statusEl.style.background = '#1b5e20';
        statusEl.style.color = '#a5d6a7';
    } else {
        statusEl.textContent = 'Neaktivní';
        statusEl.style.background = '#333';
        statusEl.style.color = '#aaa';
    }
}

// Export functions to window
window.loadFlexiBeeConfig = loadFlexiBeeConfig;
window.saveFlexiBeeConfig = saveFlexiBeeConfig;
window.testFlexiBeeConnection = testFlexiBeeConnection;
window.runFlexiBeeSync = runFlexiBeeSync;
window.updateFlexiBeeStatus = updateFlexiBeeStatus;

console.log('FlexiBee functions loaded');
