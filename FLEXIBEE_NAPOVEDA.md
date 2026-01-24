# FlexiBee Integrace - Nápověda

**Verze:** 2.0  
**Datum:** 2026-01-21

---

## 📘 Co je FlexiBee integrace?

FlexiBee integrace automaticky synchronizuje vaše faktury z účetního systému **ABRA Flexi (FlexiBee)** do Cashflow aplikace. Díky tomu máte vždy aktuální přehled o příjmech a výdajích bez nutnosti ručního zadávání.

### Hlavní funkce

✅ **Vydané faktury** - Automaticky importuje vaše vydané faktury jako příjmy  
✅ **Přijaté faktury** - Automaticky importuje přijaté faktury jako výdaje  
✅ **Automatická synchronizace** - Každou hodinu se data automaticky aktualizují  
✅ **Bezpečné připojení** - Šifrované heslo a zabezpečené HTTPS spojení  

---

## ⚙️ Jak FlexiBee integrace funguje?

### 1. Připojení k FlexiBee serveru

Aplikace se připojuje k vašemu FlexiBee serveru pomocí REST API s těmito údaji:

- **Host:** Adresa vašeho FlexiBee serveru (např. `https://demo.flexibee.eu:5434`)
- **Společnost:** Kód vaší společnosti v FlexiBee
- **Uživatel:** Přihlašovací jméno
- **Heslo:** Přihlašovací heslo (automaticky šifrované)

### 2. Synchronizační proces

1. **Načtení konfigurace** - Aplikace načte vaše přihlašovací údaje (heslo je automaticky dešifrováno)
2. **Připojení k FlexiBee** - Navázání zabezpečeného HTTPS spojení
3. **Stažení vydaných faktur** - Načtení všech vydaných faktur (příjmy) změněných od poslední synchronizace
4. **Stažení přijatých faktur** - Načtení všech přijatých faktur (výdaje) změněných od poslední synchronizace
5. **Detekce duplicit** - Kontrola, zda faktura již není v databázi
6. **Uložení do databáze** - Nové faktury se přidají, existující se aktualizují
7. **Aktualizace časové značky** - Uložení času poslední synchronizace

💡 **Chytrá synchronizace:** Při první synchronizaci se stáhnou faktury za posledních 365 dní. Při dalších synchronizacích se stahují pouze změny od poslední synchronizace.

---

## 🔄 Mapování dat z FlexiBee

### Vydané faktury (Příjmy)

| FlexiBee pole | Cashflow pole | Popis |
|---------------|---------------|-------|
| `code` | Zdroj | Číslo faktury |
| `datSplat` | Datum | Datum splatnosti |
| `sumCelkem` | Částka | Celková částka (kladná) |
| `firma.showAs` | Zákazník | Název zákazníka |
| `varSym` | Var. symbol | Variabilní symbol |
| `popis` | Popis | Popis faktury |
| `uhrazeno` | Stav platby | Zaplaceno/Nezaplaceno |

### Přijaté faktury (Výdaje)

| FlexiBee pole | Cashflow pole | Popis |
|---------------|---------------|-------|
| `code` | Zdroj | Číslo faktury |
| `datSplat` | Datum | Datum splatnosti |
| `sumCelkem` | Částka | Celková částka (záporná) |
| `firma.showAs` | Dodavatel | Název dodavatele |
| `varSym` | Var. symbol | Variabilní symbol |
| `popis` | Popis | Popis faktury |
| `uhrazeno` | Stav platby | Zaplaceno/Nezaplaceno |

---

## ✨ Nové funkce (Verze 2.0)

### 🔐 Šifrování hesel
**Status:** ✅ AKTIVNÍ

Vaše heslo je automaticky šifrováno pomocí AES algoritmu a bezpečně uloženo.

### 🔄 Retry mechanismus
**Status:** ✅ AKTIVNÍ

Při výpadku spojení se automaticky provede až 3 pokusy o připojení s exponenciálním zpožděním (2s, 4s, 8s).

### 📄 Stránkování
**Status:** ✅ AKTIVNÍ

Podpora pro velké datasety (10000+ faktur) bez timeoutu. Data se stahují po 100 záznamech.

### 🔔 Webhooks
**Status:** ⚠️ PŘIPRAVENO

Real-time synchronizace pomocí webhooků (vyžaduje konfiguraci FlexiBee serveru).

---

## 🚀 Plánovaná vylepšení

### 📅 Krátkodobá vylepšení (1-2 týdny)

- **Changes API** - Efektivnější sledování změn pomocí FlexiBee Changes API
- **Progress bar** - Vizuální indikátor průběhu synchronizace v UI
- **Email notifikace** - Automatické upozornění při chybách synchronizace
- **Detailní logy** - Rozšířené logování pro lepší diagnostiku
- **Konfigurovatelný interval** - Možnost nastavit frekvenci automatické synchronizace

### 📅 Střednědobá vylepšení (1-2 měsíce)

- **Obousměrná synchronizace** - Možnost vytvářet a upravovat faktury v FlexiBee přímo z Cashflow
- **Multi-company podpora** - Správa více společností v jedné aplikaci
- **Dashboard pro FlexiBee** - Přehledné statistiky synchronizace, historie změn
- **Bankovní transakce** - Automatický import bankovních výpisů z FlexiBee
- **Pokladní transakce** - Import hotovostních plateb z FlexiBee pokladny
- **Párování plateb** - Automatické párování plateb s fakturami
- **Webhook aktivace** - Plná podpora real-time synchronizace

### 📅 Dlouhodobá vylepšení (3+ měsíce)

- **Offline režim** - Lokální cache dat s automatickou synchronizací při obnovení připojení
- **AI predikce cashflow** - Inteligentní predikce budoucího cashflow na základě historických dat
- **Detekce anomálií** - Automatická detekce neobvyklých plateb a upozornění
- **Mobilní aplikace** - Nativní aplikace pro Android a iOS s offline podporou
- **API pro třetí strany** - Veřejné API pro integraci s dalšími systémy
- **Pokročilé reporty** - Grafické reporty, analýzy trendů, srovnání období
- **Multi-měnová podpora** - Automatické přepočty kurzů a správa více měn

---

## 📊 Výkonnostní charakteristiky

### Synchronizační čas

| Počet faktur | Verze 1.0 | Verze 2.0 | Zlepšení |
|--------------|-----------|-----------|----------|
| 100 faktur | ~2-5 sekund | ~2 sekundy | ✅ Rychlejší |
| 1000 faktur | ~20-30 sekund | ~25 sekund | ✅ Stabilnější |
| 10000 faktur | ❌ Timeout/Crash | ~3-5 minut | ✅ Funguje! |

### Bezpečnostní vylepšení

| Funkce | Verze 1.0 | Verze 2.0 |
|--------|-----------|-----------|
| Uložení hesla | ❌ Plain text | ✅ AES šifrování |
| Retry při výpadku | ❌ Ne | ✅ 3 pokusy |
| Velké datasety | ❌ Timeout | ✅ Stránkování |
| Real-time sync | ❌ Ne | ⚠️ Připraveno |

---

## 🔧 Řešení častých problémů

### ❌ Chyba: "Připojení selhalo"

**Možné příčiny:**
- Nesprávná adresa FlexiBee serveru
- Špatné přihlašovací údaje
- FlexiBee server není dostupný
- Firewall blokuje připojení

**Řešení:**
1. Zkontrolujte URL adresu (musí začínat `https://`)
2. Ověřte uživatelské jméno a heslo
3. Použijte tlačítko "Test připojení"
4. Kontaktujte administrátora FlexiBee serveru

### ❌ Chyba: "Žádná data synchronizována"

**Možné příčiny:**
- Žádné nové faktury od poslední synchronizace
- Nesprávný časový filtr

**Řešení:**
1. Zkontrolujte, zda máte v FlexiBee nové faktury
2. Zkuste resetovat čas poslední synchronizace
3. Použijte manuální synchronizaci

### ❌ Chyba: "Timeout"

**Řešení:**

Verze 2.0 automaticky řeší timeouty pomocí:
- Retry mechanismus (3 pokusy)
- Stránkování (po 100 záznamech)
- Delší timeout (30 sekund)

---

## 📞 Podpora a dokumentace

### Dostupná dokumentace

- **`FLEXIBEE_QUICKSTART.md`** - Rychlý průvodce nastavením (5 min čítanie)
- **`FLEXIBEE_ENHANCEMENTS.md`** - Kompletní technická dokumentace (45 min)
- **`FLEXIBEE_ANALYSIS.md`** - Podrobná analýza architektury (30 min)
- **`ARCHITECTURE_DIAGRAMS.md`** - Vizuální diagramy a datové toky
- **`IMPLEMENTATION_SUMMARY.md`** - Souhrn implementace a testy

### Web nápověda

Otevřete v prohlížeči: **http://localhost:8888/flexibee/help**

Zde najdete interaktivní nápovědu s:
- Vizuálními diagramy
- Barevným zvýrazněním
- Interaktivními příklady
- Detailními tabulkami

---

## 🎯 Jak začít?

### Krok 1: Nastavení FlexiBee

1. Přihlaste se do aplikace Cashflow
2. Klikněte na **⚙️ Nastavení**
3. Vyberte **FlexiBee**
4. Vyplňte přihlašovací údaje:
   - Host: `https://vas-flexibee-server.cz:5434`
   - Společnost: `vase_spolecnost`
   - Uživatel: `admin`
   - Heslo: `vaše_heslo`
5. Klikněte na **Test připojení**
6. Pokud je test úspěšný, zaškrtněte **Povolit automatickou synchronizaci**
7. Klikněte na **Uložit**

### Krok 2: První synchronizace

1. Klikněte na tlačítko **Synchronizovat nyní**
2. Počkejte na dokončení (může trvat několik minut při první synchronizaci)
3. Zkontrolujte importované faktury v hlavním přehledu

### Krok 3: Automatická synchronizace

Od této chvíle se faktury budou automaticky synchronizovat každou hodinu.

---

## ✅ Kontrolní seznam

- [ ] FlexiBee je správně nakonfigurován
- [ ] Test připojení proběhl úspěšně
- [ ] První synchronizace dokončena
- [ ] Automatická synchronizace je povolena
- [ ] Faktury se zobrazují v přehledu
- [ ] Heslo je šifrované (zkontrolujte v `flexibee_config.json`)

---

**Verze:** 2.0  
**Poslední aktualizace:** 2026-01-21  
**Status:** ✅ Production Ready

Pro více informací navštivte webovou nápovědu: **http://localhost:8888/flexibee/help**
