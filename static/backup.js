// Backup management functions

async function createBackup() {
    try {
        const response = await fetch('/api/backup/create', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            alert(`✓ ${data.message}\nSoubor: ${data.filename}`);
            loadBackups();
        } else {
            alert(`✗ Chyba: ${data.message}`);
        }
    } catch (error) {
        alert('✗ Chyba připojení');
    }
}

async function loadBackups() {
    try {
        const response = await fetch('/api/backup/list');
        const data = await response.json();

        const list = document.getElementById('backups-list');
        if (!list) return;

        if (data.backups.length === 0) {
            list.innerHTML = '<p style="color: var(--text-secondary);">Žádné zálohy</p>';
        } else {
            list.innerHTML = data.backups.map(b => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; 
                            background: rgba(118, 118, 128, 0.12); border-radius: 8px; margin-bottom: 8px;">
                    <div>
                        <strong>${b.filename}</strong><br>
                        <small style="color: var(--text-secondary);">
                            ${new Date(b.created).toLocaleString('cs-CZ')} | ${(b.size / 1024).toFixed(2)} KB
                        </small>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="downloadBackup('${b.filename}')" style="padding: 6px 12px; font-size: 12px;">
                            ⬇️ Stáhnout
                        </button>
                        <button onclick="restoreBackup('${b.filename}')" style="padding: 6px 12px; font-size: 12px; background: var(--accent-primary);">
                            🔄 Obnovit
                        </button>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load backups:', error);
    }
}

function downloadBackup(filename) {
    window.location.href = `/api/backup/download/${filename}`;
}

async function restoreBackup(filename) {
    if (!confirm(`Opravdu chcete obnovit zálohu?\n\n${filename}\n\nAktuální data budou přepsána!`)) {
        return;
    }

    try {
        const response = await fetch('/api/backup/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });

        const data = await response.json();

        if (data.status === 'success') {
            alert('✓ Záloha byla obnovena\n\nStránka se obnoví...');
            window.location.reload();
        } else {
            alert(`✗ Chyba: ${data.message}`);
        }
    } catch (error) {
        alert('✗ Chyba připojení');
    }
}

async function uploadBackup() {
    const input = document.getElementById('backup-upload-input');
    if (!input.files.length) {
        alert('Vyberte soubor zálohy');
        return;
    }

    if (!confirm('Opravdu chcete nahrát a obnovit tuto zálohu?\n\nAktuální data budou přepsána!')) {
        return;
    }

    const formData = new FormData();
    formData.append('file', input.files[0]);

    try {
        const response = await fetch('/api/backup/restore', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.status === 'success') {
            alert('✓ Záloha byla obnovena\n\nStránka se obnoví...');
            window.location.reload();
        } else {
            alert(`✗ Chyba: ${data.message}`);
        }
    } catch (error) {
        alert('✗ Chyba připojení');
    }
}

async function loadBackupConfig() {
    try {
        const response = await fetch('/api/backup/config');
        const config = await response.json();

        document.getElementById('backup-enabled').checked = config.enabled;
        document.getElementById('backup-interval').value = config.interval_hours;
        document.getElementById('backup-max').value = config.max_backups;
    } catch (error) {
        console.error('Failed to load backup config:', error);
    }
}

async function saveBackupConfig() {
    const config = {
        enabled: document.getElementById('backup-enabled').checked,
        interval_hours: parseInt(document.getElementById('backup-interval').value),
        max_backups: parseInt(document.getElementById('backup-max').value)
    };

    try {
        const response = await fetch('/api/backup/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });

        const data = await response.json();

        if (data.status === 'success') {
            alert('✓ Konfigurace byla uložena');
        } else {
            alert(`✗ Chyba: ${data.message}`);
        }
    } catch (error) {
        alert('✗ Chyba připojení');
    }
}
