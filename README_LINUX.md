# Instalace Cashflow Dashboard na Linux

Tento návod vás provede instalací aplikace na Linux server (např. Ubuntu, Debian, Raspberry Pi).

## 1. Příprava
Nahrajte celou složku `cashflow_app` na váš server (např. přes SCP, FTP nebo Git).

Příklad:
```bash
scp -r cashflow_app user@server:/home/user/
```

## 2. Instalace
Připojte se na server, jděte do složky aplikace a spusťte instalační skript.

```bash
cd cashflow_app
chmod +x install.sh
./install.sh
```

Tento skript:
- Vytvoří virtuální prostředí Pythonu (`venv`).
- Nainstaluje potřebné knihovny (`flask`, `pandas`, atd.).
- Vytvoří adresářovou strukturu pro data (`data/vstupy/...`).
- Vytvoří spouštěcí skript `run.sh`.

## 3. Spuštění
Pro manuální spuštění použijte:
```bash
./run.sh
```
Aplikace poběží na portu **8888**. Otevřete v prohlížeči `http://IP_ADRESA_SERVERU:8888`.

### Výchozí přihlašovací údaje
Po první instalaci se přihlaste pomocí:
- **Uživatelské jméno:** `admin`
- **Heslo:** `admin`

⚠️ **DŮLEŽITÉ:** Po prvním přihlášení změňte heslo v Nastavení → Správa uživatelů!

## 4. Automatické spouštění (Systemd Service)
Pokud chcete, aby aplikace běžela na pozadí a startovala automaticky po restartu:

1. Otevřete soubor `cashflow.service` a upravte cesty a uživatele:
   - `User=...` (váš linux uživatel, např. `ubuntu`)
   - `WorkingDirectory=...` (absolutní cesta, např. `/home/ubuntu/cashflow_app`)
   - `ExecStart=...` (cesta k pythonu ve venv, např. `/home/ubuntu/cashflow_app/venv/bin/python3 app.py`)

2. Zkopírujte soubor do systémových služeb:
   ```bash
   sudo cp cashflow.service /etc/systemd/system/
   ```

3. Aktivujte službu:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable cashflow
   sudo systemctl start cashflow
   ```

4. Zkontrolujte stav:
   ```bash
   sudo systemctl status cashflow
   ```

## Poznámky
- Ujistěte se, že firewall (pokud používáte) povoluje port 8888.
  - `sudo ufw allow 8888`
