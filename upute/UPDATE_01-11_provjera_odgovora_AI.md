# 📐 Provjera kratkog odgovora u v2 — točne upute za prijenos iz v1

**Datum:** 1.11.2026. · **Autor:** DeepSeek · **Cilj:** `caki-testovi` (v2)
**Stanje:** v1 je **gotov i testiran** (`provjera_odgovora.py`, 85 testova). Ovaj dokument je
**radni nalog** za prijenos istog ponašanja u v2 — po njemu radi drugi bot, redom, bez improvizacije.

> **Pročitaj cijeli dokument prije prve izmjene.** Redoslijed koraka nije proizvoljan: korak 2 se
> oslanja na korak 1, a korak 6 (profesorska provjera) je ono zbog čega cijela stvar ima smisla.

---

## 0. Što se prenosi — u tri rečenice

1. **Zapis ≠ vrijednost.** Sustav je točne odgovore označavao netočnima jer je uspoređivao zapis
   (`\mathrm{8.8605}` prema `8.8605`). Vidi §1.
2. **AI je drugo mišljenje, ne rješavač.** Poziva se samo kad je odgovor „blizu", dobiva ključ i
   smije reći samo „isti je / nije isti". Nikad ne računa rješenje. Vidi §2.
3. **Sumnja ide profesoru, ne u nulu.** Kad se ne može odlučiti, zadatak dobiva oznaku `?` i čeka
   Cakija — **nikad automatska nula**. Vidi §5–§6.

---

## 1. Nalaz (Caki, 31.10.2026.) — 13 stvarnih redaka iz `Rezultati_testova`

Stupac **`Upisao`** = ono što je učenik upisao, **`Točno`** = ključ iz baze. Sve donje je **ISTI
odgovor, drugi zapis** — a sustav je dao 0 bodova.

| # | Upisano (učenik) | Ključ (baza) | Što je bilo krivo |
|---|---|---|---|
| 1 | `\mathrm{8.8605}` | `8.8605` | `\mathrm{}` omotač se nije skidao |
| 2 | `\mathrm{\frac{3-a}{3a}}` | `$\frac{3-a}{3a}$` | omotač **s ugniježđenim** zagradama |
| 3 | `\mathrm{\sqrt[4]{a}}` | `$\sqrt[4]{a}$` | isto + `$…$` |
| 4 | `\mathrm{11466}` | `11466` | isto |
| 5 | `\mathrm{58}` | `58 eura` | mjerna jedinica samo u ključu |
| 6 | `\mathrm{(-\infty,-3) U (11,+\infty)}` | `$(-\infty,-3) \cup (11,+\infty)$` | `U` prema `\cup`, `\infty` |
| 7 | `\mathrm{\frac78}` | `$x=\frac{7}{8}$` | `\frac78` bez zagrada + `x=` |
| 8 | `\mathrm{8}` | `8 °C` | oznaka stupnjeva |
| 9 | `\mathrm{7.5}` | `za više od 7.5 km` | ključ opisan riječima |
| 10 | `\mathrm{65\degree50^{\prime}}` | `65°50' ili 114°10'` | `\degree`, `\prime`, **dva prihvaćena rješenja** |
| 11 | `\mathrm{254.55}` | `254.55 m` | metri |
| 12 | `\mathrm{32\pi}` | `32\pi cm^2` | `\pi` + `cm^2` |
| 13 | `\mathrm{116.25}` | `116.25 litara` | litre riječju |

**Kriterij prihvaćanja:** svi redci iz tablice moraju završiti kao **`tocno`**, deterministički,
**bez AI-ja** (vidi §7).

---

## 2. Tri pravila (i ništa izvan njih)

```
odgovor
   │
   ├─ prazan ─────────────────────────────────► „prazno"
   ├─ ključ prazan / prosireni_odgovor ───────► „ceka"  (čeka Cakija)
   │
   ├─ 1. ZAPIS (deterministički) ──── isti ────► „tocno"   (izvor: zapis / broj / jedinica)
   │      omotači, razlomci, °, ', ∪, ∞, jedinice
   │
   ├─ 2. AI (samo ako je „blizu") ── isti ─────► „tocno"   (izvor: ai)
   │      vidi ključ, ne računa ga         └───► „netocno" (izvor: ai, sigurnost visoka)
   │
   └─ 3. SUMNJA ──────────────────────────────► „sumnja"  → 🧑‍🏫 Caki
          nema AI-ja, AI nije siguran, jedinica se razlikuje
```

**Tvrde granice koje se NE smiju probiti:**

- AI **nikad** ne dobiva zadatak bez ključa i **nikad** ne smije vratiti broj/rješenje.
- Ako je vrijednost **dokazivo drugačija** (oba se daju izračunati i razlikuju se), AI se **ne pita**
  — to je `netocno`. Npr. `\frac{8}{4}` prema `\frac{8}{3}`.
- AI smije promijeniti odluku **samo** uz `sigurnost = "visoka"`. Srednja/niska = `sumnja`.
- `sumnja` **nije** nula. Bodovi su 0 samo privremeno; profesor ih može dati.

---

## 3. Što v2 već ima — i što točno fali

v2 je **ispred v1** po strukturi: `caki-testovi/ocjenjivanje.py` već ima tri sloja
(`string` → `SymPy` → `AI`) i izvor odluke (`IZVOR_STRING/SYMPY/AI/PROFESOR/NEMA`). **Ne rušiti taj
kostur** — dopunjuje se.

| # | Fali u v2 | Gdje | Zašto je važno |
|---|---|---|---|
| G1 | `normalizuj()` ne skida `\mathrm{}` s **ugniježđenim** zagradama, ne zna `\frac78`, `\degree`, `\prime`, `\cup`, `\infty` | `ocjenjivanje.py:44-64` | redci 1–13 iz §1 i dalje padaju |
| G2 | nema trećeg stanja — `ocjeni_zadatak` vraća samo `tocno`/`netocno`/`?`; **`sumnja` se ne razlikuje od „ne znam"** | `ocjenjivanje.py:276-311` | profesor ne vidi zašto |
| G3 | **AI sloj je mrtav kod** — `prijedlog_ai` traži `pozovi(uputa, pitanje)`, a `ai_pomoc.pitaj` ima potpis `(poruke, *, kljuc, tajna, …)`; `provedba.predaj` se poziva s `dopusti_ai=False` | `ocjenjivanje.py:219-255`, `ekran_ucenika.py:247,256,343` | AI se **nikad** ne izvrši |
| G4 | **nitko ne pokazuje `ceka_profesora`** — izračuna se i baci | `app.py` (nema reference) | nema reda čekanja; učenik dobije 0 zauvijek |
| G5 | `ocijeni_rucno` **ne preračuna** `Pokusaji.bodovi` nakon ručne odluke i ima `placeholder` poziv koji ništa ne radi | `provedba.py:352-364` | profesor popravi zadatak, a ukupni bodovi ostanu stari |

---

## 4. Korak 1 — `provjera_odgovora.py` u v2 (kopija, bez prepisivanja)

**Uzmi datoteku 1:1:**
`CAKI_razvoj\caki-booking-termina\provjera_odgovora.py` → `CAKI_razvoj\caki-testovi\provjera_odgovora.py`

- **Ne prepisuj po sjećanju i ne „popravljaj" ju.** Ona je već testirana (85 testova u
  `testovi/test_provjera_odgovora.py`). Ako treba izmjena — mijenja se u v1 i kopira, inače se
  v1 i v2 raziđu.
- Modul **nema** Streamlit, gspread ni vlastite ovisnosti (samo `json`, `re`, `difflib`;
  `requests` se uvozi lijeno u `napravi_pozivac`). Zato radi i u v2 bez izmjena.
- U docstringu samo dopiši rečenicu: *„U v2 je ovo treći sloj ocjenjivanja (`ocjenjivanje.py`);
  kopija je iz v1 od 1.11.2026."* — kod ne diraj.

**Javno sučelje koje se koristi (ne mijenjati imena):**

| Funkcija | Vraća |
|---|---|
| `normalizuj(tex)` | string za usporedbu |
| `razdvoji_jedinicu(s)` | `("254.55", "cm")` |
| `brojevi(tekst)` | `[7.5]` |
| `blizu(kljuc, odgovor)` | `bool` — je li kandidat za AI/profesora |
| `uporedi(kljuc, odgovor)` | `{"status", "izvor", "zasto"}` — **deterministički** |
| `odluci(kljuc, odgovor, *, tekst="", pozovi=None, dopusti_ai=True)` | isto, ali s AI-jem |
| `ai_uporedi(kljuc, odgovor, tekst="", pozovi=None)` | `{"tocno","sigurnost","zasto"}` ili `None` |
| `napravi_pozivac(secrets)` | callable ili `None` (nema ključa) |
| `tocno(kljuc, odgovor)` | `bool` |

**Statusi:** `tocno` · `netocno` · `sumnja` · `prazno` · `ceka`.
**Izvori:** `zapis` · `broj` · `jedinica` · `ai` · `sumnja`.

---

## 5. Korak 2 — `ocjenjivanje.py`: spojiti slojeve

### 5.1 `normalizuj()` (linija 44)

Zamijeni **tijelo** pozivom na zajednički modul; ime i potpis ostaju (koristi ih i `tipovi.py`):

```python
import provjera_odgovora as provjera

def normalizuj(tekst) -> str:
    """Usporediv oblik (tijelo: `provjera_odgovora.normalizuj`)."""
    return provjera.normalizuj(tekst)
```

`JEDINICE` i `bez_varijable()` **ostaju** u datoteci (koristi ih `tipovi.py` i stariji pozivi), ali
ih `normalizuj` više ne treba.

### 5.2 `tocan_string()` (linija 86) — prvi sloj

```python
def tocan_string(kljuc, odgovor, tolerancija: float = 1e-9) -> bool:
    """Prvi sloj: je li odgovor jednak ključu nakon normalizacije (zapis, broj ili jedinica)."""
    return provjera.uporedi(kljuc, odgovor)["status"] == provjera.STATUS_TOCNO
```

`tipovi.py:232,246` zove `ocjenjivanje.tocan_string(a, b)` — potpis ostaje isti, ništa se tamo ne mijenja.

### 5.3 `ocjeni_zadatak()` (linija 276) — spoj tri sloja

Zamijeni **cijelu funkciju** ovim (komentari su dio naloga — objasnit će sljedećem čitatelju zašto):

```python
def ocjeni_zadatak(zadatak: dict, odgovor, *, pozovi=None, dopusti_ai: bool = True) -> dict:
    """Vrati {"tocno", "bodovi", "max", "izvor", "sigurnost", "zasto", "status"}.

    1.11.2026.: odluku vodi `provjera_odgovora` (zapis → broj/jedinica → AI → sumnja).
    `izvor` = "?" znači „čeka profesora" i to je JEDINO što smije dati nulu bez odluke.
    """
    max_b = model.broj((zadatak or {}).get("bodovi"), 1)
    odg = model.tekst(odgovor)
    kljuc = model.tekst((zadatak or {}).get("odgovor"))

    if not odg:
        return {"tocno": False, "bodovi": 0.0, "max": max_b, "izvor": IZVOR_NEMA,
                "sigurnost": "", "zasto": "nema odgovora", "status": "prazno"}

    if je_izbor(zadatak):
        tocno = tocan_izbor(zadatak, odg)
        return {"tocno": tocno, "bodovi": max_b if tocno else 0.0, "max": max_b,
                "izvor": IZVOR_STRING, "sigurnost": "visoka", "zasto": "",
                "status": "tocno" if tocno else "netocno"}

    # 2. sloj (SymPy) ostaje PRIJE AI-ja: matematički ekvivalentni izrazi ne troše poziv
    if provjera.tocno(kljuc, odg) or tocan_sympy(kljuc, odg):
        return {"tocno": True, "bodovi": max_b, "max": max_b, "izvor": IZVOR_STRING,
                "sigurnost": "visoka", "zasto": "", "status": "tocno"}

    rez = provjera.odluci(kljuc, odg, tekst=model.tekst((zadatak or {}).get("tekst")),
                          pozovi=pozovi, dopusti_ai=dopusti_ai)
    if rez["status"] == provjera.STATUS_TOCNO:                 # AI je rekao „isti je"
        return {"tocno": True, "bodovi": max_b, "max": max_b, "izvor": IZVOR_AI,
                "sigurnost": "visoka", "zasto": rez["zasto"], "status": "tocno"}
    if rez["status"] == provjera.STATUS_SUMNJA:
        return {"tocno": False, "bodovi": 0.0, "max": max_b, "izvor": "?",
                "sigurnost": "niska", "zasto": rez["zasto"] or "sličan zapis — provjeri ručno",
                "status": "sumnja"}
    if rez["status"] in (provjera.STATUS_PRAZNO, provjera.STATUS_CEKA):
        return {"tocno": False, "bodovi": 0.0, "max": max_b, "izvor": "?", "sigurnost": "",
                "zasto": rez["zasto"], "status": rez["status"]}
    return {"tocno": False, "bodovi": 0.0, "max": max_b, "izvor": IZVOR_STRING,
            "sigurnost": "visoka", "zasto": rez["zasto"], "status": "netocno"}
```

**Pravilo koje se ne smije izgubiti:** dvostruki poziv `provjera.tocno(...)` + `tocan_sympy(...)`
znači da SymPy ostaje **ispred** AI-ja. Tako se za `\sqrt{8}` prema `2\sqrt{2}` ne troši ni jedan
AI poziv.

### 5.4 `ocjeni_zadatke()` (linija 351)

Dodaj u svaki detalj `status` i `zasto` (već se vraćaju iz `ocjeni_zadatak`) te broj `sumnja`:

```python
        if r["status"] == "sumnja":
            sumnja += 1
```
i u povratak `{"bodovi", "maks", "detalji", "ceka_profesora": ceka, "sumnja": sumnja}`.

---

## 6. Korak 3 — `provedba.predaj()`: uključiti AI i zapisati razlog

`caki-testovi/provedba.py:288`:

1. **Ništa u potpisu ne mijenjati** (`pozovi=None, dopusti_ai=True` već postoji).
2. `_upisi_ocjene()` (linija 333) već piše `izvor_ocjene` — dovoljno je da `ocjeni_zadatak` vrati
   `"?"` za `sumnja` (radi po §5.3). **Dopuni** da u `komentar` ide razlog:

```python
            "komentar": model.tekst(d.get("zasto")) if model.tekst(d.get("izvor")) == "?" else "",
```

3. U povratku `predaj()` dodaj `"sumnja": ocjena.get("sumnja", 0)` uz postojeći `ceka_profesora`.

4. **⚠️ `dopusti_ai=False` u `ekran_ucenika.py` (linije 247, 256, 343)** — to je namjerno za
   **pregled** (`Student View`, Cakijev dry-run). Ali **prava predaja** mora dobiti AI. Provjeri
   svaki poziv `provedba.predaj(...)` i:
   - **ostavi** `dopusti_ai=False` gdje je `dry=True` / pregled,
   - **dodaj** `pozovi=ai_pomoc.pozovi_za_ocjenu(st.secrets)` i `dopusti_ai=... is not None` gdje
     učenik stvarno predaje.

### 6.1 `ai_pomoc.py` — adapter (G3)

Dodaj na kraj `caki-testovi/ai_pomoc.py` (postojeće funkcije **ne diraj**):

```python
def pozovi_za_ocjenu(secrets, timeout: int = 15):
    """`pozovi(uputa, pitanje) -> {"tekst"}` za `ocjenjivanje.prijedlog_ai`, ili None.

    Zašto adapter: `pitaj()` prima GOTOVU listu poruka i traži ključ/tajnu, a ocjenjivanje traži
    `pozovi(uputa, pitanje)`. Bez ovoga AI sloj nikad ne radi (G3 iz uputa 1.11.2026.).
    """
    vrsta = ima_kljuc(secrets)
    if not vrsta:
        return None
    tajna = model.tekst(secrets.get("DEEPSEEK_API_KEY" if vrsta == "deepseek" else "ANTHROPIC_API_KEY"))

    def pozovi(uputa: str, pitanje: str) -> dict:
        tekst, greska = pitaj([{"role": "system", "content": uputa},
                               {"role": "user", "content": pitanje}],
                              kljuc=vrsta, tajna=tajna, timeout=timeout)
        if greska:
            raise RuntimeError(greska)          # `ai_uporedi` to pretvori u „ne znam" → sumnja
        return {"tekst": tekst}

    return pozovi
```

**Ugovor je time isti kao u v1** (`provjera_odgovora.napravi_pozivac`) — ako se ikad pređe na v1
modul, ništa se ne mijenja.

**Sigurnosna mreža (obavezno):** u `predaj()` ograniči broj AI poziva na **4 po pokušaju** i
ukupno **20 s**. Predaja testa ne smije visjeti zbog mreže. (v1 to ima u `testovi_online.ocjeni`
preko `max_ai` i `budzet_s` — prepiši isti obrazac.)

---

## 7. Korak 4 — Testovi (prije nego se dira sučelje)

Novi `testovi/test_v2_provjera_odgovora.py`. **Obavezno:**

1. **13 redaka iz §1** — parametrizirano, `ocjeni_zadatak` mora vratiti `tocno` i `bodovi == max`.
2. **Isti 13 redaka kroz `provjera.odluci(..., dopusti_ai=False)`** — svi `tocno` (dokaz da AI nije
   potreban; ako neki padne, normalizacija je nepotpuna).
3. **Negativni:** `3` prema `4` → `netocno`; `8 m` prema `8 cm` → `sumnja` (ne `tocno`!);
   `\frac{1}{2}` prema `\frac{1}{3}` → `netocno`.
4. **AI stub:** `pozovi` koji vraća `{"tocno": True, "sigurnost": "visoka"}` → `tocno`, `izvor = ai`;
   `niska` → `sumnja` i `izvor = "?"`; AI baca grešku → `sumnja` (nikad pad ocjene).
5. **Brojač poziva:** za 10 „blizu" zadataka s `max_ai=2` AI se zove **točno 2** puta.
6. **Nema AI-ja za očito pogrešno:** `3` prema `4` ne troši nijedan poziv.
7. **SymPy ispred AI-ja:** `\sqrt{8}` prema `2\sqrt{2}` → `tocno`, `izvor != ai`, 0 poziva.
8. **`provedba.predaj`** (lažni sheet, kao u postojećim testovima): pokušaj sa `sumnja` dobiva
   `Ocjene_zadataka.izvor_ocjene = "?"` i `komentar` s razlogom; `Pokusaji.bodovi` je privremen.
9. **`promaseni`/statistika** ne smiju „sumnju" brojati kao promašaj.

---

## 8. Korak 5 — 🧑‍🏫 Profesorska provjera (G4) — bez ovoga posao nije gotov

Danas `ceka_profesora` nitko ne prikazuje. Treba **jedan novi modul + jedna kartica u `app.py`**.

### 8.1 `caki-testovi/provjera_ocjena.py` (novi modul, bez Streamlita)

```python
"""Red čekanja za profesora: sve ocjene s `izvor_ocjene = "?"`.

Zašto modul: `app.py` je već narastao (v. ARHITEKTURA.md §7) — logika ide ovdje, sučelje u app.py.
"""
TAB = tablice.TAB_OCJENE

def na_cekanju(sheet, definicija_id: str = "") -> list[dict]:
    """Ocjene koje čekaju odluku, s podacima za prikaz (učenik, zadatak, odgovor, ključ, razlog)."""

def primijeni(sheet, pokusaj_id: str, zadatak_id: str, *, tocno: bool, profesor: str = "",
              razlog: str = "") -> dict:
    """Profesorova odluka: `provedba.ocijeni_rucno(...)` + PRERAČUN `Pokusaji.bodovi`."""

def preracunaj_pokusaj(sheet, pokusaj_id: str) -> dict:
    """Zbroji `Ocjene_zadataka.bodovi` u `Pokusaji.bodovi`/`bodovi_max` (G5)."""
```

`preracunaj_pokusaj` je **obavezan** — `provedba.ocijeni_rucno` mijenja samo ocjenu zadatka, pa bi
ukupni bodovi ostali stari. (I usput: `provedba.py:361` ima `ok = tablice.azuriraj(...)  # placeholder`
— taj mrtvi poziv obriši.)

### 8.2 `app.py` — nova kartica

- U `st.tabs([...])` (linija 290–291) dodaj **`"🧑‍🏫 Provjera"`** na kraj i pridruži `tab_provjera`.
- Kartica: brojač **„Čeka provjeru: N"**, popis (učenik · test · zadatak · odgovor · ključ · zašto),
  za svaki red **✅ točno / ❌ netočno / ⏭ preskoči**, jedan gumb **„💾 Spremi odluke"**.
- Prazno stanje: *„Nema što provjeravati — sve ocjene su zaključene."* (UX_PRAVILA.md)
- Ako odluka mijenja bodove, nakon spremanja **osvježi keš** (`st.cache_data.clear()`).

### 8.3 Učenik u međuvremenu

`rjesavanje.poruka_o_cekanju(broj)` već postoji — provjeri da se **stvarno prikazuje** u pregledu
nakon predaje i da `izvor_ocjene == "?"` dolazi iz `Ocjene_zadataka`. Učenik **ne smije** vidjeti
„0 bodova" bez objašnjenja.

---

## 9. Kriteriji prihvaćanja (Caki provjerava ovim redom)

- [ ] 13 redaka iz §1 → **svi `tocno`**, bez AI-ja.
- [ ] `8 m` prema `8 cm` → **`sumnja`**, ne `tocno` i ne tiho `netocno`.
- [ ] `3` prema `4` → `netocno`, **0 AI poziva**.
- [ ] AI isključen (nema ključa) → sumnje idu profesoru, **ništa se ne ruši**.
- [ ] Nakon predaje s jednom sumnjom: učenik vidi **„1 zadatak čeka provjeru profesora"**.
- [ ] U 🧑‍🏫 Provjeri: vidi se odgovor **i ključ i razlog**; ✅ podigne bodove i **preračuna ukupno**.
- [ ] U `Izmjene_ocjena` postoji zapis (tko, kada, prije/poslije, razlog) — GDPR trag.
- [ ] Cijeli v2 paket testova **ne pada** (osim poznatih padova iz TRACKER-a).

---

## 10. Što NE raditi

1. **Ne prepisivati `provjera_odgovora.py`** — kopirati datoteku.
2. **Ne dirati shemu** (`Ocjene_zadataka`, `Pokusaji`) — `izvor_ocjene = "?"` i `komentar` već
   postoje. Novi stupac nije potreban.
3. **Ne slagati novi red čekanja** (`Dodjele`/`Status`) — provjera se čita iz `Ocjene_zadataka`.
4. **Ne zvati AI za svaki pogrešan odgovor** — samo za `blizu`, najviše 4 po pokušaju.
5. **Ne mijenjati `Statistika_zadataka`** (append-only, §12.11.3) i ne dirati `smije_urediti()`,
   `novi_id()`, `_upisi_rucno()` izvan opisa u §8.1 — v. MASTER §12.4.
6. **Ne spajati ovaj posao s prelaskom v1→v2 (4.11.)** — ovo je popravak ocjenjivanja, ne migracija.

---

## 11. Za Cakija — što ovo mijenja u praksi

- Točan odgovor napisan **drugim zapisom** više ne nosi 0 bodova.
- Ako sustav nije siguran, **ne odlučuje sam** — zadatak ide tebi, s odgovorom, ključem i razlogom.
- AI troši pozive **samo na granične slučajeve** (nekoliko po testu), i može se isključiti
  (`AI_PROVJERA_ODGOVORA = "Ne"` u v1; u v2 analogno u Secrets).
- Sve odluke ostaju **zapisane** (`izvor_ocjene` + `Izmjene_ocjena`) — to je odgovor na prigovor
  „zašto je moje dijete dobilo 0".

---

## 12. Preračun **već predanih** testova i ručni ispravak (dodano 1.11.2026., 14:00)

**Cakijevo pitanje (1.11.2026.):** „Jel moguće ispraviti već predane testove — bodovanje koje nije
pravilno napravljeno? Gdje se ispravka radi i gdje mogu promijeniti bodovanje za zadatak? Ne vidim
opcije." — Odgovor je **da**, i to je u v1 napravljeno istog dana. **v2 to mora imati također**, jer
će i on imati povijesne pokušaje ocijenjene starom logikom.

### 12.1 Dvije stvari, ne jedna

| Što | Kada | Što dira |
|---|---|---|
| **🧮 Preračun** (automatski) | cijeli test ocijenjen starom logikom; svi zadaci odjednom | ponovno ocijeni iz sačuvanih odgovora |
| **✏️ Ručni ispravak** (po zadatku) | jedan učenik, jedan zadatak; djelomični bodovi | jedna ocjena |

### 12.2 Preračun — kako radi (i zašto je pošten)

1. **Izvor istine su sačuvani odgovori**, ne ponovno rješavanje: `Pokusaji.odgovori_json` +
   **zamrznuti** zadaci u `Pokusaji.zadaci_json` (v2 ih već čuva od 30.10., §12.11.4). Ako
   `zadaci_json` fali, uzmi zadatke iz `Definicije_testova` i **napiši upozorenje** da se koristi
   trenutna verzija testa.
2. Ponovno se pozove `ocjenjivanje.ocjeni_zadatke(...)` (ista funkcija kao kod predaje) — nema
   drugog puta ocjenjivanja, inače preračun i stvarna ocjena mogu se razići.
3. **Preskoči** pokušaje koje je profesor već ručno dirao (`Ocjene_zadataka.izvor_ocjene` =
   `profesor` ili postoji zapis u `Izmjene_ocjena`) — inače preračun pregazi profesorovu odluku.
   Caki to može svjesno nadjačati kvačicom.
4. **Prvo prikaz, pa upis.** Tablica: učenik · prije (b) · poslije (b) · prije (%) · poslije (%).
   Upis ide tek uz kvačicu „potvrđujem" i gumb; piše se **samo**: `Ocjene_zadataka` (tocno, bodovi,
   izvor_ocjene, komentar), `Pokusaji.bodovi`/`bodovi_max`, i `Dnevnik_radnji` zapis
   (`preracun`, tko, koliko). **`odgovori_json` se nikad ne mijenja.**
5. Nakon upisa: `st.cache_data.clear()` (inače ekran pokazuje stare bodove) + zapis u
   `Izmjene_ocjena` s razlogom `preracun` (GDPR trag: „zašto se ocjena promijenila").

### 12.3 Ručni ispravak — bilo koji pokušaj, ne samo „čeka"

Cakijeva primjedba je bila da **nije bilo opcije**: u v1 je stranica prikazivala samo rezultate sa
statusom `ceka`, pa rezultat ocijenjen prije tog statusa nije imao gdje biti ispravljen. U v2:
popis **svih** pokušaja → odabir → svi zadaci s odgovorom i ključem → odluka
**✅ točno · 🟡 djelomično (upis bodova) · ❌ netočno · — ostavi kako je —** → jedan gumb.

- Djelomični bodovi: `bodovi` je 0…`max`; `tocno` je istina **samo** ako je dosegnut `max`.
- Svaka izmjena ide kroz `izmjene_ocjena.zapisi(...)` (`povod = profesor_sam_primijetio`).
- **Obavezno** preračunaj `Pokusaji.bodovi` iz `Ocjene_zadataka` (G5 iz §3 — u v2 to danas ne radi).

### 12.4 Zamka koja je uhvaćena u v1 (prenesi je)

`@st.cache_data` / `@st.cache_resource` **ne uključuju u ključ keša parametre koji počinju s `_`**.
Ako funkcija glasi `def _podaci(_id: str)`, podaci dvaju različitih Sheetova se zamijene.
Piši `def _podaci(sheet_id: str)`.

### 12.5 Testovi (obavezno)

1. Preračun 13 redaka iz §1: stari rezultat (svi `netocno`) → **svi `tocno`**, 0 → puni bodovi.
2. Preračun je **idempotentan** — drugi prolaz nema promjena.
3. Preračun **preskače** ručno provjerene; `odgovori_json` prazan → poruka „nema sačuvanih odgovora".
4. Upis preračuna **ne dira** `odgovori_json` (provjeri adrese ćelija).
5. Ručni ispravak s `bodovi = 1.5` od `max = 3` → 1.5 b, `tocno = False`, ukupno preračunato.
6. Ručni ispravak iznad `max` se reže na `max`.
7. **Ručni ispravak radi i za pokušaj koji nije `ceka`** (to je bio Cakijev nalaz).
8. AppTest stranice: preračun pokaže „Mijenja se: 1" i **ništa ne upiše** bez potvrde.

---

📌 **COMMIT:** mapa `caki-testovi` → repo `caki-testovi` → grana **main** → ✅ ide uživo nakon
Push + Reboot — **ali tek kad su ispunjeni svi kriteriji iz §9.**
📌 **COMMIT:** `testovi/test_v2_provjera_odgovora.py` — nije u gitu, samo lokalno.
