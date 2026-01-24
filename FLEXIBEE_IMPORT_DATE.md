# FlexiBee Import Date Feature

## Popis

Nová funkcia umožňuje nastaviť konkrétny dátum, od ktorého sa majú importovať faktúry z FlexiBee.

## Použitie

### V UI (Nastavenia → FlexiBee)

1. Otvorte **Nastavenia**
2. Prejdite na tab **FlexiBee API**
3. V sekcii **Synchronizace** nájdete nové pole:
   - **📅 Importovat faktury od data**
   - Vyberte dátum pomocou date pickera
   - Ak pole necháte prázdne, použije sa predvolených 365 dní

### Ako to funguje

#### Pri prvej synchronizácii (keď `last_sync` neexistuje):
- Ak je nastavený `import_from_date`: použije sa tento dátum
- Ak nie je nastavený: použije sa dátum pred 365 dňami

#### Pri ďalších synchronizáciách:
- Vždy sa použije `last_sync` (dátum poslednej synchronizácie)
- `import_from_date` sa ignoruje (už sa synchronizuje len od poslednej zmeny)

### Príklady

**Príklad 1: Import faktúr od začiatku roka**
```
import_from_date: 2024-01-01
→ Importujú sa všetky faktúry od 1.1.2024
```

**Príklad 2: Import faktúr za posledných 6 mesiacov**
```
import_from_date: 2024-07-01
→ Importujú sa faktúry od 1.7.2024
```

**Príklad 3: Bez nastavenia**
```
import_from_date: (prázdne)
→ Importujú sa faktúry za posledných 365 dní
```

## Technické detaily

### Frontend (flexibee.js)
- Pridané pole `import_from_date` do `loadFlexiBeeConfig()`
- Pridané pole `import_from_date` do `saveFlexiBeeConfig()`

### Backend (flexibee_sync.py)
- Upravená metóda `sync_invoices()` v `FlexiBeeConnector`
- Logika:
  ```python
  if not last_sync:
      if import_from_date:
          start_date = parse(import_from_date)
      else:
          start_date = now - 365 days
  else:
      start_date = last_sync
  ```

### API Endpoint
- `/api/flexibee/config` (GET/POST)
- Automaticky ukladá a načítava `import_from_date`

## Reset synchronizácie

Ak chcete znova importovať faktúry od nastaveného dátumu:

1. V súbore `data/flexibee_config.json` vymažte riadok `"last_sync"`
2. Alebo spustite:
   ```bash
   python -c "import json; config = json.load(open('data/flexibee_config.json')); config.pop('last_sync', None); json.dump(config, open('data/flexibee_config.json', 'w'), indent=4)"
   ```
3. Spustite synchronizáciu znova

## Testovanie

Spustite test:
```bash
python test_import_date.py
```

Všetky testy by mali prejsť ✅
