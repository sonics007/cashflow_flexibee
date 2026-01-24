# 💰 Cashflow Dashboard s FlexiBee Integráciou

Moderná webová aplikácia pre sledovanie cash flow s automatickou synchronizáciou faktúr z FlexiBee účtovného systému.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)

## ✨ Hlavné funkcie

### 📊 Cash Flow Dashboard
- **Kalendárny prehľad** príjmov a výdajov
- **Automatický výpočet** aktuálneho stavu účtu
- **Farebné rozlíšenie** - zelená (príjmy), červená (výdaje)
- **Detailný prehľad** transakcií pre každý deň
- **Responzívny dizajn** - funguje na mobile, tablete aj desktope

### 🔄 FlexiBee Integrácia
- **Automatická synchronizácia** faktúr z FlexiBee
- **Smart Sync** - sťahuje len nové/zmenené faktúry
- **Rate Limiting** - ochrana pred preťažením API (50 req/min)
- **Adaptive Delay** - inteligentné spomalenie pri chybách
- **Šifrované heslá** - bezpečné uloženie FlexiBee credentials
- **Retry mechanizmus** - automatické opakovanie pri zlyhaní
- **Pagination** - spracovanie veľkých objemov dát

### 📥 Import faktúr
- **Excel import** (.xlsx, .xls) - prijaté aj vystavené faktúry
- **Automatické parsovanie** - inteligentné rozpoznanie stĺpcov
- **FlexiBee sync** - automatický import z účtovného systému
- **Nastaviteľný dátum** - import faktúr od konkrétneho dátumu

### 👥 Správa používateľov
- **Multi-user** - podpora viacerých používateľov
- **Role-based access** - admin a user role
- **Bezpečné heslá** - bcrypt hashing
- **Audit log** - sledovanie akcií používateľov

### 💾 Zálohovanie
- **Automatické zálohy** - nastaviteľný interval
- **Manuálne zálohy** - vytvorenie zálohy na požiadanie
- **Restore** - obnovenie z lokálnej zálohy alebo servera
- **Správa záloh** - mazanie starých záloh

## 🚀 Rýchla inštalácia (Linux)

### ⚡ One-Command Install (Odporúčané)

Najrýchlejší spôsob - jeden príkaz urobí všetko:

```bash
curl -sSL https://raw.githubusercontent.com/sonics007/cashflow_flexibee/main/quick-install.sh | sudo bash
```

Alebo s `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/sonics007/cashflow_flexibee/main/quick-install.sh | sudo bash
```

**Čo skript urobí:**
1. ✅ Nainštaluje všetky dependencies (Python, git, SQLite)
2. ✅ Klonuje repozitár z GitHubu
3. ✅ Vytvorí virtual environment
4. ✅ Nainštaluje Python packages
5. ✅ Nakonfiguruje systemd service
6. ✅ Nastaví FlexiBee (ak chcete)
7. ✅ Spustí aplikáciu

**Skript sa opýta na:**
- 📁 Inštalačný adresár (default: `/opt/cashflow`)
- 🔌 Port (default: `8887`)
- 🔄 FlexiBee konfigurácia (voliteľné)

---

### 📦 Manuálna inštalácia

Ak preferujete manuálnu inštaláciu:

### Predpoklady
- Python 3.8+
- pip
- SQLite3

### Inštalácia

```bash
# 1. Klonujte repozitár
git clone https://github.com/sonics007/cashflow_flexibee.git
cd cashflow_flexibee/cashflow_app_v2

# 2. Spustite inštalačný skript
chmod +x install.sh
./install.sh

# 3. Spustite aplikáciu
./run.sh
```

Aplikácia bude dostupná na `http://localhost:8887`

### Výchozí přihlašovací údaje
- **Username:** `admin`
- **Password:** `admin`

⚠️ **DŮLEŽITÉ:** Po prvním přihlášení změňte heslo v Nastavení → Správa uživatelů!

## 🐳 Docker (voliteľné)

```bash
# Spustenie cez Docker
docker-compose up -d
```

## ⚙️ Konfigurácia FlexiBee

1. Otvorte **Nastavenia → FlexiBee API**
2. Vyplňte údaje:
   - **URL Serveru:** `https://demo.flexibee.eu:5434`
   - **Firma:** `demo_sro`
   - **Používateľ:** váš FlexiBee API user
   - **Heslo:** vaše FlexiBee API heslo
3. Kliknite na **Otestovat připojení**
4. Ak je test úspešný, kliknite na **Uložit nastavení**
5. Povoľte **Automatickú synchronizáciu** (voliteľné)
6. Kliknite na **Spustit nyní** pre manuálnu synchronizáciu

## 📖 Dokumentácia

- [README_LINUX.md](README_LINUX.md) - Detailný návod pre Linux
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Štruktúra projektu
- [FLEXIBEE_NAPOVEDA.md](FLEXIBEE_NAPOVEDA.md) - FlexiBee nápoveda (CZ)
- [FLEXIBEE_RATE_LIMITING.md](FLEXIBEE_RATE_LIMITING.md) - Rate limiting
- [FLEXIBEE_IMPORT_DATE.md](FLEXIBEE_IMPORT_DATE.md) - Import od dátumu

## 🛠️ Technológie

- **Backend:** Python 3.8+, Flask 2.0+
- **Database:** SQLite3
- **Frontend:** Vanilla JavaScript, CSS3
- **FlexiBee API:** REST API s autentifikáciou
- **Encryption:** Fernet (symmetric encryption)
- **Password Hashing:** Werkzeug bcrypt

## 📁 Štruktúra projektu

```
cashflow_app_v2/
├── app.py                      # Hlavná Flask aplikácia
├── database.py                 # DB schéma a inicializácia
├── db_wrapper.py               # DB abstrakčná vrstva
├── flexibee_sync.py            # FlexiBee synchronizácia
├── flexibee_rate_limiter.py    # Rate limiting
├── templates/                  # HTML šablóny
│   ├── index.html
│   ├── login.html
│   └── settings_modal.html
├── static/                     # CSS, JS, obrázky
│   ├── style.css
│   ├── script.js
│   └── flexibee.js
└── data/                       # Databáza a konfigurácia
    ├── cashflow.db
    └── flexibee_config.json
```

## 🔒 Bezpečnosť

- ✅ Šifrované heslá (bcrypt)
- ✅ Šifrovaná FlexiBee konfigurácia (Fernet)
- ✅ Session management
- ✅ CSRF protection
- ✅ SQL injection protection (parametrizované queries)
- ✅ Audit log všetkých akcií

## 🐛 Riešenie problémov

### FlexiBee sa nepripojí
1. Skontrolujte URL servera (musí obsahovať `https://` a port)
2. Overte používateľské meno a heslo
3. Skontrolujte, či je API povolené vo FlexiBee
4. Pozrite logy: `journalctl -u cashflow -f`

### Aplikácia nefunguje po reštarte
```bash
# Skontrolujte stav služby
sudo systemctl status cashflow

# Reštartujte službu
sudo systemctl restart cashflow

# Pozrite logy
sudo journalctl -u cashflow -n 50
```

## 🤝 Prispievanie

Contributions sú vítané! Prosím:
1. Forkujte repozitár
2. Vytvorte feature branch (`git checkout -b feature/AmazingFeature`)
3. Commitujte zmeny (`git commit -m 'Add some AmazingFeature'`)
4. Pushujte do branchu (`git push origin feature/AmazingFeature`)
5. Otvorte Pull Request

## 📝 Changelog

### v2.0.0 (2026-01-24)
- ✨ Pridaná FlexiBee integrácia
- ✨ Modal editácia faktúr (bez refresh)
- ✨ Full-width zobrazenie faktúr
- ✨ Automatické čistenie názvov firiem (odstránenie "code:")
- ✨ Nastaviteľný dátum importu faktúr
- 🐛 Opravené parsovanie dátumov z FlexiBee
- 🐛 Opravené sticky header v tabuľkách
- 📝 Vylepšená dokumentácia
- 🧹 Cleanup nepotrebných súborov

### v1.0.0 (2025-12-15)
- 🎉 Prvé vydanie
- ✨ Základný cash flow dashboard
- ✨ Excel import faktúr
- ✨ Správa používateľov
- ✨ Zálohovanie

## 📄 Licencia

Tento projekt je licencovaný pod MIT licenciou - pozrite [LICENSE](LICENSE) pre detaily.

## 👨‍💻 Autor

**sonics007**
- GitHub: [@sonics007](https://github.com/sonics007)

## 🙏 Poďakovanie

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [FlexiBee](https://www.flexibee.eu/) - Účtovný systém
- [SQLite](https://www.sqlite.org/) - Database

---

⭐ Ak sa vám projekt páči, dajte mu hviezdičku na GitHube!
