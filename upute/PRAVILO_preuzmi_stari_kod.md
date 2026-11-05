# ♻️ PRAVILO: prvo pogledaj stari kod

**Cakijeva uputa 26.10.2026.:** *„Uvijek usporedi stari kod i vidi da li možeš ga iskoristiti."*

Ovo pravilo vrijedi za **svaki** novi zahvat u `caki-testovi`. Cilj nije „sve novo", nego **najmanje
novog koda koji radi**.

---

## Kako se provodi (3 koraka, prije pisanja)

1. **Popis:** postoji li već modul/funkcija za to? (v. tablicu dolje)
2. **Provjera oblika:** je li upotrebljivo kao **modul** ili je Streamlit **stranica**
   (stranica se ne može importati — izvršava `st.` kod uvoza). Ako je stranica: **izdvoji funkcije**.
3. **Zapis u `UPDATE` dokumentu:** što je preuzeto, a što napisano novo **i zašto**.

## Gdje stari kod živi

| Mapa | Što je unutra |
|---|---|
| `caki-baza-zadataka/` | baza zadataka (113 KB pipeline), **test builder** (77 KB), `testovi_online` (35 KB), `predmet_config`, `test_biblioteka_izvora`, `ocjenjivanje_pretpregled`, `formule`, `skupine_zadataka`, `podjela_zadataka`, `radovi_admin`, `uputa_u_aplikaciji` |
| `caki-baza-zadataka/pages/` | stranice: `2_test_builder` (PDF preko pdflatexa!), `9_testovi`, `10_pretpregled_testa`, `15_radovi`, `13_pomoc_pri_ucenju`, `14_formule` |
| `caki-booking-termina/` | **portal učenika**: `testovi_online` (53 KB — rješavanje), `kratki_odgovor_unos`, `slike_zadataka`, `ai_pomoc`, `radovi` (12 KB), `obavijesti`, `portal_ui` |

## Stanje: što je preuzeto, a što ne

### ✅ Preuzeto (i to je dobro)

| Funkcija u v2 | Odakle | Kako |
|---|---|---|
| `slike_zadataka.py` | `caki-booking-termina/slike_zadataka.py` | **kopija modula** + tolerantni JSON |
| `secrets_json.py` | `caki-baza-zadataka` | kopija, ojačana (pametni navodnici, `\n`) |
| `tex_test.py` (PDF testa) | `pages/2_test_builder.py` | **AST izdvajanje**: `escape_outside_math`, `izgradi_opcije_blok`, `izgradi_kategorije_tex`, `formatiraj_opciju`, `pronadji_neuparene_dolare` + `main_test_template.tex` + `caki-style.sty` + `packages.txt` |
| `builder.pripremi_za_prikaz` | `escape_outside_math` (stari) | preuzeta logika escapiranja izvan formule |
| `unos_odgovora.py` | `kratki_odgovor_unos.py` | ista ideja (MathLive + fallback) |
| `upute.py` | `uputa_u_aplikaciji.py` | isti obrazac (upute u aplikaciji) |

### 🔁 Napisano novo — i **zašto**

| Funkcija u v2 | Zašto nije preuzeto | Bi li se dalo preuzeti? |
|---|---|---|
| `definicije`, `dodjele`, `provedba` | stari sustav **nema** test kao zapis (samo redci po učenicima) | ne — to je nova arhitektura |
| `tablice`, `model` | stari kod čita Sheet izravno na 20 mjesta | namjerno: jedan sloj za budući Supabase |
| filtri/paginacija (`builder`) | u starom su dijelom stranice, dijelom u tijelu petlje | **da** — `test_biblioteka_izvora.py` i `filtriraj_zadatke_za_skriptu.py` treba pregledati |
| analitika (p, r, α) | stari ima `ocjenjivanje_pretpregled.py` (9 KB) | **provjeriti** — možda ima dio statistike |
| PDF izvještaj (reportlab) | stari **nema** izvještaj za roditelje | ne |

## Kandidati za sljedeće preuzimanje (po vrijednosti) — ažurirano 05.11.2026. (Claude)

**Provjereno uživo u kodu (ne samo po sjećanju) — status stupac je novi, prijašnja tablica je bila
zastarjela: #1, #3 i #5 su već odavno gotovi, samo nitko nije ovdje prekrižio.**

| # | Stari modul | Što bi riješio u v2 | Trud | Status (05.11.) |
|---|---|---|---|---|
| 1 | `pages/15_radovi.py` + `radovi.py` (portal, 12 KB) | 📷 radovi — pregled, potvrda, prikaz | mali | ✅ **Gotovo** — `radovi.py` postoji, uvezen i korišten u `app.py` i `pages/1_Ucenik.py` |
| 2 | `ocjenjivanje_pretpregled.py` | 📈 statistika zadatka (usporediti s `analitika.py`, uzeti bolje) | mali | ⚠️ **Vjerojatno nadiđeno** — v2 ima `statistika.py`+`analitika.py`+`analiza_rezultata.py` (698 redaka nasuprot 166 u v1); nije provjereno pokriva li baš SVE što je stari modul pokazivao, ali po opsegu je veći. Nije hitno. |
| 3 | `test_biblioteka_izvora.py` + `filtriraj_zadatke_za_skriptu.py` | filtri po **biblioteci izvora** | mali | ✅ **Gotovo** — `builder.filtriraj()` ima `izvor=`/`potpoglavlje=`, UI u `app.py` L442 (`st.multiselect("Biblioteka izvora", …)`). Docstring u `builder.py` je zastario (još piše „nedostaju" — ispraviti) |
| 4 | `testovi_online.py` (portal, 53 KB) | logika rješavanja (prekid, nastavak, istek) — usporediti s `provedba.py` | srednji | 🟡 **Otvoreno, nije hitno** — v2 ima vlastiti `provedba.py`/`ekran_ucenika.py` (autosave, nastavak); usporedba red-po-red nije rađena, moguće da postoje sitni UX detalji vrijedni preuzimanja (npr. server-side rok koji preživi F5 — provjeriti ima li v2 to) |
| 5 | `skupine_zadataka.py` (18 KB) | skupine zadataka (a), (b), (c) — v2 ih još ne podržava | srednji | ✅ **Gotovo** — `skupine.py` eksplicitno kaže „preuzeto doslovno", uvezen u `banka.py` i `tex_test.py` |
| 6 | `formule.py` (11 KB) | formule/LaTeX pomoć u editoru | mali | ❌ **Još nema** — nema `formule.py` ni ekvivalenta `pages/14_formule.py` u v2. Zadano DeepSeeku: `ZADACI/ZADATAK_06_brisanje_rok_formule.md` §3 |
| 7 | `predmet_config.py` | zaglavlje PDF-a po predmetu (`MATEMATIKA`, `FIZIKA`…) — sada je fiksno | mali | ❌ **Još nema** — `tex_test.py` ima `predmet_zaglavlje: str = "MATEMATIKA"` kao TVRDI default, nitko ga nigdje u `app.py`/`pages/1_Ucenik.py` ne postavlja na nešto drugo. Svaki v2 test (čak i fizika, ako ikad bude) dobije "MATEMATIKA" na PDF-u. Nije u ZADATAK_06 — dodati u sljedeći zadatak prije nego v2 preuzme i druge predmete. |

## Novi nalazi (05.11.2026., Claude) — nisu bili na staroj listi

| Što | Gdje | Trud |
|---|---|---|
| Brisanje testa iz UI-a (`definicije.obrisi()` postoji, ali se nigdje ne zove) | `app.py` | mali — ZADATAK_06 §1 |
| Rok (`rok_od`/`rok_do`) ne provjerava je li već prošao prije objave/izmjene | `app.py` L361–365, L744–752 | mali — ZADATAK_06 §2 |
| **HITNO:** "Zadaj pojedinom učeniku" zna upisati krivi/prazan `ucenik_id` (dokazano na živom Sheetu, slučaj OH3229) | `app.py` (Objavi, Pojedini učenici) | nepoznato dok se ne reproducira — ZADATAK_06 §0 |

## Pravilo za buduće izvještaje

Svaki `UPDATE_*.md` mora imati odjeljak **„Preuzeto / novo"** s ovom tablicom. Ako je nešto napisano
novo, a stari kod je imao isto — **mora pisati zašto**.
