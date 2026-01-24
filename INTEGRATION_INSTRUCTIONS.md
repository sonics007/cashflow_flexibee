# Inštrukcie na integráciu nového settings modalu

## Krok 1: Nahraďte starý settings modal

V súbore `templates/index.html` nájdite sekciu:
```html
<!-- Modal pre správu používateľov -->
<div class="modal-overlay" id="settings-modal">
...
</div>
```

A nahraďte ju obsahom zo súboru `templates/settings_modal.html`

## Krok 2: Pridajte CSS štýly

CSS štýly sú už zahrnuté v `settings_modal.html` na konci súboru.

## Krok 3: JavaScript funkcie

Všetky potrebné funkcie sú už v `static/script.js`:
- showSettingsTab()
- loadUploadedFiles()
- confirmResetDB()
- confirmRestartServer()
- createBackup()
- loadBackups()
- downloadBackup()
- restoreBackup()
- uploadBackup()
- loadBackupConfig()
- saveBackupConfig()

## Krok 4: Automatické zálohovanie (voliteľné)

Pre automatické zálohovanie pridajte do `app.py`:

```python
import schedule
import threading
import time

def backup_scheduler():
    """Background thread for automatic backups"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def setup_auto_backup():
    """Setup automatic backup based on config"""
    from database import load_backup_config, create_backup, cleanup_old_backups
    
    config = load_backup_config()
    if config.get('enabled'):
        interval = config.get('interval_hours', 24)
        max_backups = config.get('max_backups', 30)
        
        def auto_backup():
            print(f"[AUTO-BACKUP] Creating backup...")
            create_backup()
            cleanup_old_backups(max_backups)
            print(f"[AUTO-BACKUP] Backup completed")
        
        schedule.every(interval).hours.do(auto_backup)
        
        # Start scheduler thread
        scheduler_thread = threading.Thread(target=backup_scheduler, daemon=True)
        scheduler_thread.start()
        print(f"[AUTO-BACKUP] Enabled - every {interval} hours, max {max_backups} backups")

# V main bloku:
if __name__ == '__main__':
    setup_auto_backup()  # Pridať pred app.run()
    ...
```

## Krok 5: Reštart servera

Po úpravách reštartujte server.

## Testovanie

1. Prihláste sa ako admin
2. Kliknite na "⚙️ Nastavení"
3. V ľavom menu kliknite na "💾 Správa DB"
4. Vyskúšajte:
   - Vytvorenie zálohy
   - Zobrazenie zoznamu záloh
   - Stiahnutie zálohy
   - Nastavenie automatických záloh

## Štruktúra súborov

```
cashflow_app/
├── app.py                          # Hlavný Flask súbor
├── database.py                     # SQLite databáza + zálohovanie
├── migrate_to_db.py               # Migračný skript (už spustený)
├── data/
│   ├── cashflow.db                # SQLite databáza
│   ├── backups/                   # Zálohy
│   │   ├── backup_20260118_123000.db
│   │   └── ...
│   └── backup_config.json         # Konfigurácia
├── templates/
│   ├── index.html                 # Hlavná stránka
│   ├── login.html                 # Prihlásenie
│   ├── settings_modal.html        # Nový settings modal (použiť)
│   └── backup_section.html        # Sekcia záloh (už zahrnuté)
└── static/
    ├── script.js                  # Všetky JS funkcie
    ├── style.css                  # Štýly
    ├── settings.js                # Settings funkcie (už v script.js)
    └── backup.js                  # Backup funkcie (už v script.js)
```
