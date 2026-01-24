// Settings menu functions
function showSettingsTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.settings-tab').forEach(tab => tab.style.display = 'none');
    document.querySelectorAll('.settings-menu-item').forEach(item => item.classList.remove('active'));

    // Show selected tab
    document.getElementById(`tab-${tabName}`).style.display = 'block';
    document.getElementById(`menu-${tabName}`).classList.add('active');

    // Load data for specific tabs
    if (tabName === 'users') {
        loadUsers();
    } else if (tabName === 'files') {
        loadUploadedFiles();
    }
}

async function loadUploadedFiles() {
    try {
        const response = await fetch('/api/uploaded_files');
        const data = await response.json();

        const prijateList = document.getElementById('files-prijate-list');
        const vydaneList = document.getElementById('files-vydane-list');

        if (data.prijate.length === 0) {
            prijateList.innerHTML = '<p style="color: var(--text-secondary);">Žádné soubory</p>';
        } else {
            prijateList.innerHTML = data.prijate.map(f => `
                <div style="padding: 8px; border-bottom: 1px solid var(--border-color);">
                    📄 ${f}
                </div>
            `).join('');
        }

        if (data.vydane.length === 0) {
            vydaneList.innerHTML = '<p style="color: var(--text-secondary);">Žádné soubory</p>';
        } else {
            vydaneList.innerHTML = data.vydane.map(f => `
                <div style="padding: 8px; border-bottom: 1px solid var(--border-color);">
                    📄 ${f}
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load files:', error);
    }
}

async function confirmResetDB() {
    if (!confirm('⚠️ VAROVÁNÍ!\n\nOpravdu chcete vymazat celou databázi?\n\nTato akce:\n- Vymaže všechny transakce\n- Vymaže počáteční stav účtu\n- NELZE ji vrátit zpět!\n\nPokračovat?')) {
        return;
    }

    if (!confirm('Jste si naprosto jistí? Toto je poslední varování!')) {
        return;
    }

    try {
        const response = await fetch('/api/reset_db', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            alert('✓ Databáze byla vymazána');
            closeSettingsModal();
            fetchData();
        } else {
            alert(`✗ Chyba: ${data.message}`);
        }
    } catch (error) {
        alert('✗ Chyba připojení');
    }
}

async function confirmRestartServer() {
    if (!confirm('Opravdu chcete restartovat server?\n\nVšichni uživatelé budou odpojeni.')) {
        return;
    }

    try {
        await fetch('/api/restart_server', { method: 'POST' });
        alert('Server se restartuje...\n\nObnovte stránku za několik sekund.');
        closeSettingsModal();
    } catch (error) {
        // Expected - server is restarting
        setTimeout(() => {
            window.location.reload();
        }, 3000);
    }
}
