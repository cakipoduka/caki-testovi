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

## Kandidati za sljedeće preuzimanje (po vrijednosti)

| # | Stari modul | Što bi riješio u v2 | Trud |
|---|---|---|---|
| 1 | `pages/15_radovi.py` + `radovi.py` (portal, 12 KB) | 📷 radovi — pregled, potvrda, prikaz | mali |
| 2 | `ocjenjivanje_pretpregled.py` | 📈 statistika zadatka (usporediti s `analitika.py`, uzeti bolje) | mali |
| 3 | `test_biblioteka_izvora.py` + `filtriraj_zadatke_za_skriptu.py` | filtri po **biblioteci izvora** | mali |
| 4 | `testovi_online.py` (portal, 53 KB) | logika rješavanja (prekid, nastavak, istek) — usporediti s `provedba.py` | srednji |
| 5 | `skupine_zadataka.py` (18 KB) | skupine zadataka (a), (b), (c) — v2 ih još ne podržava | srednji |
| 6 | `formule.py` (11 KB) | formule/LaTeX pomoć u editoru | mali |
| 7 | `predmet_config.py` | zaglavlje PDF-a po predmetu (`MATEMATIKA`, `FIZIKA`…) — sada je fiksno | mali |

## Pravilo za buduće izvještaje

Svaki `UPDATE_*.md` mora imati odjeljak **„Preuzeto / novo"** s ovom tablicom. Ako je nešto napisano
novo, a stari kod je imao isto — **mora pisati zašto**.
