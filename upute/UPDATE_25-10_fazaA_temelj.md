# 📘 UPDATE 25.10.2026. — Faza A: temelj sustava testiranja

**Status:** kod radi, 37 testova prolazi, aplikacija deployana na Streamlit
**Grana:** `main` (novi repo `caki-testovi`)
**Prethodnik:** `CAKI_razvoj/upute/MASTER_SUSTAV_TESTIRANJA.md` (v2.0) i `ANALIZA_24-10_sustavi_testiranja.md` (v1.0, istraživanje)

---

## 1. Što je napravljeno

Nova aplikacija u **zasebnom repou** — stara tri repoa nisu dirana (nula rizika za ono što radi).

| Modul | Što rješava |
|---|---|
| `tablice.py` | **jedini sloj koji zna gdje podaci žive** — Sheets danas, Supabase kasnije |
| `veza.py` | otvara Sheetove, odabir servisnog računa (testni vs dijeljeni) |
| `model.py` | pretvorbe (broj/datum/JSON), ID-evi, vrijeme |
| `banka.py` | čita 20.000+ zadataka, mapira u zamrznuti oblik, filtri, **🎬 video** |
| `definicije.py` | **test kao zapis**, Student View, A/B miješanje, provjere prije objave |
| `dodjele.py` | **kome je test poslan**, rok po učeniku, dopuna bez duplikata |
| `provedba.py` | pokušaj, **autosave**, predaja, ručna ocjena |
| `ocjenjivanje.py` | tri sloja: string → SymPy → AI (samo predlaže) → `?` profesoru |
| `grupe.py` | grupe Upisa i kante Mature |
| `upute.py` | upute unutar aplikacije (nikad zasebna stranica) |
| `app.py` | 4 kartice: 🧪 Testovi · 👥 Objavi · 📊 Rezultati · ⚙️ Postavke |

## 2. Cakijeve odluke ugrađene u kod

| Odluka | Gdje je u kodu |
|---|---|
| test se ne vidi svima, zadano **nacrt** | `definicije.STANJA`, `status="nacrt"` |
| **dodavanje nakon objave** je nova dodjela | `dodjele.dodaj()` — idempotentno |
| **učenik dodan poslije roka** dobiva rok od dodjele | `dodjele.rok_dodjele()` |
| rok **po grupi** ako je izvedivo | rok na dodjeli ima prednost pred rokom testa |
| **A/B**: isti sadržaj, izmiješan redoslijed | `definicije.izmijesaj()` + `varijanta_seed` |
| **Student View po testu** | `student_view_json` + `smije_vidjeti()` |
| rješenja/video **tek nakon roka** | `smije_vidjeti(..., rok_prosao=True)` |
| **AI samo predlaže**, profesor odlučuje | `ocjenjivanje.prijedlog_ai()` + `izvor_ocjene` |
| **video iz baze**, nakon testa | `banka.video_za()`, stupac `video_url` (postoji od prije) |
| baza se **ne mijenja** | `banka` je bez ijedne funkcije pisanja u `Zadaci` |

## 3. Sigurnost prema živoj bazi

Aplikacija radi na **pravom CRM Sheetu**, zato:

- **Upis je zadano isključen** (`tablice.PISANJE = False`) — sve funkcije pisanja bacaju
  `PermissionError` dok se ne uključi prekidačem ili secretom `V2_UPIS`.
- **Baza zadataka se ne mijenja** — čita se, ništa se ne dodaje.
- **„Pripremi tabove"** stvara samo nove tabove i traži izričitu potvrdu.
- **`.gitignore`** blokira `secrets.toml`, `__pycache__` i `.venv`.

## 4. Bugovi nađeni i popravljeni (sve uhvaćeno testovima)

| # | Bug | Kako je nađen | Popravak |
|---|---|---|---|
| 1 | `'dict' object has no attribute 'module'` | Caki na deployu | `service_account_from_dict()` umjesto `authorize(dict)` |
| 2 | JSON u Secrets pada na „pametnim" navodnicima | Caki na deployu | `secrets_json` sada popravlja pametne navodnike, `\n`, `=`, zareze |
| 3 | `2x+1=5` u bazi, a učenik upiše `2` → netočno | vlastiti test | usporedba preko rješenja jednadžbe (SymPy) + skidanje varijable |
| 4 | dvostruka predaja iz dva taba | vlastiti test | provjera **stvarnog** statusa u Sheetu, ne u sesiji |
| 5 | `__pycache__` ušao u prvi commit | pregled repoa | `.gitignore` |
| 6 | miješanje samo odgovora miješalo i zadatke | vlastiti test | odvojeno `izmijesaj_odgovore()` |

## 5. Testovi

| Datoteka | Broj | Što pokriva |
|---|---|---|
| `testovi/test_v2_temelj.py` | 31 | model, tablice, definicije, dodjele (uključivo Cakijev bug), ocjenjivanje, provedba, banka, sigurnosna kočnica |
| `testovi/test_v2_veza.py` | 3 | odabir tajne (testni vs dijeljeni račun), `service_account_from_dict` |
| `testovi/test_v2_app_apptest.py` | 3 | dimni test aplikacije (bez Googlea) |
| **ukupno** | **37** | svi prolaze |

Uz to: **94 testa starih sustava** prolaze — dokaz da ništa nije dirano.

## 6. Što Caki treba napraviti

1. **Commit + push** u `caki-testovi` (ako već nije): `veza.py`, `secrets_json.py`, `README.md`,
   `upute/` (ova mapa).
2. **Reboot app** na Streamlit Cloudu.
3. Provjeri **⚙️ Postavke** → „🎬 Stupac `video_url` postoji u bazi".
4. Uključi upis u bočnoj traci → **⚙️ Postavke → 🔧 Pripremi tabove**.

## 7. Sljedeće — Faza B

- ekran rješavanja za učenika: **pitanje po pitanju**, popis s napretkom
- **autosave** i nastavak nakon prekida (F5, mobitel)
- **matematički unos** (MathLive) + slike + formule
- **💡 pomoć** (AI, bez rješenja)
- **🎬 video nakon testa** (kad pregled rješenja postane dostupan)
- pregled **„kako ovo vidi učenik"** unutar iste aplikacije

**Procjena Faze B:** 7–10 radnih dana.
