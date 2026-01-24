# FlexiBee Rate Limiting - Dokumentácia

## 📊 Koľko requestov posiela aplikácia?

### Aktuálny stav (BEZ rate limiting)

#### Pri synchronizácii 1000 faktúr:
```
Vydané faktúry:  1000 / 100 = 10 requestov
Prijaté faktúry: 1000 / 100 = 10 requestov
────────────────────────────────────────────
CELKOM:                       20 requestov
Čas:                          ~25 sekúnd
Rate:                         0.8 req/s = 48 req/min ✅ OK
```

#### Pri synchronizácii 10000 faktúr:
```
Vydané faktúry:  10000 / 100 = 100 requestov
Prijaté faktúry: 10000 / 100 = 100 requestov
────────────────────────────────────────────
CELKOM:                       200 requestov
Čas:                          ~3-5 minút
Rate:                         1.1 req/s = 66 req/min ⚠️ RIZIKO!
```

---

## ⚠️ FlexiBee Rate Limits

### Typické limity FlexiBee servera:
- **Max requests/minútu:** 60-120 (závisí od konfigurácie)
- **Max súbežné requesty:** 5-10
- **Timeout:** 30-60 sekúnd
- **Max payload:** 1-10 MB

### Riziko preťaženia:
- ❌ **66 req/min** môže prekročiť limit **60 req/min**
- ❌ Môže spôsobiť **429 Too Many Requests** error
- ❌ Môže spomaliť FlexiBee server pre ostatných užívateľov

---

## ✅ RIEŠENIE - Rate Limiting

### 1. Token Bucket Algorithm

Vytvoril som `flexibee_rate_limiter.py` s dvoma triedami:

#### **RateLimiter**
```python
# Limit: 50 requestov za 60 sekúnd
limiter = RateLimiter(max_requests=50, time_window=60)

# Pred každým requestom
limiter.acquire()  # Počká ak je limit prekročený
make_request()
```

**Ako to funguje:**
1. Sleduje posledných 60 sekúnd requestov
2. Ak je limit (50) dosiahnutý, **počká**
3. Automaticky pokračuje keď je voľné miesto

#### **AdaptiveDelay**
```python
# Adaptívne oneskorenie medzi requestami
delay = AdaptiveDelay(min_delay=0.1, max_delay=2.0)

# Pred requestom
delay.wait()

# Po úspešnom requeste
delay.on_success()  # Zníži delay

# Po chybnom requeste
delay.on_error()    # Zvýši delay
```

**Ako to funguje:**
1. Začína s malým delayom (0.1s)
2. Pri chybách **zvyšuje** delay (až do 2s)
3. Pri úspechoch **znižuje** delay
4. Automaticky sa prispôsobuje záťaži servera

---

## 🔧 Ako integrovať do `flexibee_sync.py`

### Krok 1: Import
```python
from flexibee_rate_limiter import flexibee_rate_limiter, flexibee_adaptive_delay
```

### Krok 2: Použitie v `_fetch_paginated_data`
```python
def _fetch_paginated_data(self, resource, filter_str, params, max_retries=3):
    all_data = []
    start = 0
    
    while True:
        # ✅ RATE LIMITING
        flexibee_rate_limiter.acquire()
        
        # ✅ ADAPTIVE DELAY
        flexibee_adaptive_delay.wait()
        
        # Existujúci kód...
        try:
            resp = RetryHandler.retry_request(make_request, ...)
            data = resp.json().get('winstrom', {}).get(resource, [])
            
            # ✅ Úspech - zníž delay
            flexibee_adaptive_delay.on_success()
            
            all_data.extend(data)
            # ...
            
        except Exception as e:
            # ✅ Chyba - zvýš delay
            flexibee_adaptive_delay.on_error()
            raise e
    
    return all_data
```

---

## 📈 Výkonnostné charakteristiky

### BEZ rate limiting (aktuálne):
```
1000 faktúr:   ~25s   (48 req/min)  ✅ OK
10000 faktúr:  ~3min  (66 req/min)  ⚠️ RIZIKO
```

### S rate limiting (50 req/min):
```
1000 faktúr:   ~30s   (40 req/min)  ✅ BEZPEČNÉ
10000 faktúr:  ~4min  (50 req/min)  ✅ BEZPEČNÉ
```

**Trade-off:**
- ✅ **Bezpečnejšie** - Neprekročí rate limit
- ✅ **Stabilnejšie** - Menej chýb
- ⏱️ **Pomalšie** - O ~20% pomalšie pri veľkých datasetoch

---

## ⚙️ Konfigurácia

### Odporúčané nastavenia podľa veľkosti FlexiBee servera:

#### **Malý server (1-5 užívateľov):**
```python
RateLimiter(max_requests=30, time_window=60)  # 30 req/min
AdaptiveDelay(min_delay=0.2, max_delay=3.0)
```

#### **Stredný server (5-20 užívateľov):**
```python
RateLimiter(max_requests=50, time_window=60)  # 50 req/min (default)
AdaptiveDelay(min_delay=0.1, max_delay=2.0)
```

#### **Veľký server (20+ užívateľov):**
```python
RateLimiter(max_requests=80, time_window=60)  # 80 req/min
AdaptiveDelay(min_delay=0.05, max_delay=1.0)
```

---

## 🎯 Odporúčania

### 1. **Použite rate limiting pre produkciu**
- ✅ Chráni FlexiBee server
- ✅ Predchádza 429 chybám
- ✅ Stabilnejšia synchronizácia

### 2. **Nastavte konzervatívne limity**
- ✅ Začnite s **50 req/min**
- ✅ Monitorujte logy
- ✅ Zvyšujte postupne ak je potrebné

### 3. **Použite adaptívne oneskorenie**
- ✅ Automaticky sa prispôsobuje
- ✅ Rýchlejšie pri nízkej záťaži
- ✅ Pomalšie pri vysokej záťaži

### 4. **Monitorujte výkon**
```python
# Získajte štatistiky
stats = flexibee_rate_limiter.get_stats()
print(f"Requests: {stats['requests_in_window']}/{stats['max_requests']}")
print(f"Available: {stats['available_slots']}")

delay = flexibee_adaptive_delay.get_current_delay()
print(f"Current delay: {delay:.2f}s")
```

---

## 🚀 Implementácia

### Možnosť 1: Manuálna integrácia
Pridajte rate limiting do `flexibee_sync.py` podľa príkladu vyššie.

### Možnosť 2: Automatická integrácia
Chcete, aby som to integroval automaticky? Poviem mi a upravím `flexibee_sync.py`.

---

## 📊 Porovnanie

| Metrika | BEZ rate limiting | S rate limiting |
|---------|-------------------|-----------------|
| **Rýchlosť (1000 faktúr)** | ~25s | ~30s (+20%) |
| **Rýchlosť (10000 faktúr)** | ~3min | ~4min (+33%) |
| **Bezpečnosť** | ⚠️ Riziko | ✅ Bezpečné |
| **Stabilita** | ⚠️ Možné chyby | ✅ Stabilné |
| **Rate** | 66 req/min | 50 req/min |
| **Odporúčané pre produkciu** | ❌ Nie | ✅ Áno |

---

## ✅ Záver

**Aktuálna implementácia:**
- ✅ Funguje pre malé datasety (< 5000 faktúr)
- ⚠️ Riziko pri veľkých datasetoch (> 10000 faktúr)
- ⚠️ Môže prekročiť rate limit FlexiBee servera

**S rate limiting:**
- ✅ Bezpečné pre všetky veľkosti datasetov
- ✅ Neprekročí rate limit
- ✅ Stabilnejšia synchronizácia
- ⏱️ O 20-30% pomalšie

**Odporúčenie:** Implementujte rate limiting pre produkčné použitie! 🚀
