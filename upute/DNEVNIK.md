# 🗓️ Dnevnik razvoja — `caki-testovi`

Jedna linija po isporuci. Detalji su u odgovarajućem `UPDATE_*.md`.

| Datum | Faza / tema | Što je ušlo | Testovi | Izvještaj |
|---|---|---|---|---|
| 25.10.2026. | **Faza C (dopuna) — po cjelinama + CSV** | `analitika.po_cjelinama`, `najslabija_cjelina` u sažetku · tablica cjelina u 📈 Kvaliteti · **CSV izvoz** rezultata za Excel | **89** (4 nova) | `UPDATE_25-10_fazaC_kvaliteta_i_portal.md` §7 |
| 25.10.2026. | **Faza C (1. dio) — kvaliteta zadataka + stranica učenika** | `analitika` (p, r, distraktori, Cronbach α, preporuke, zaštita malog uzorka) · kartica **📈 Kvaliteta** · `pages/1_Ucenik.py` (prijava šifrom, popis, rješavanje, pregled po Student View-u) | **85** (18 novih) | `UPDATE_25-10_fazaC_kvaliteta_i_portal.md` |
| 25.10.2026. | **Faza B (2. dio) — slike, 💡 pomoć, 🎬 video** | `slike_zadataka` (Drive, tolerantan ključ) · `ai_pomoc` (bot ne daje rješenje, max 3 pitanja, odgovor ne ulazi u upit) · slika i 💡 uz zadatak · pregled rješenja po učeniku u Rezultatima | **67** (17 novih) | `UPDATE_25-10_fazaB_slike_ai_video.md` |
| 25.10.2026. | **Faza B (1. dio) — ekran rješavanja** | `ekran_ucenika` (pitanje po pitanju, autosave, predaja, pregled bez upisa) · `rjesavanje` (napredak, povratna informacija, 🎬 video uz zaštitu) · `unos_odgovora` (MathLive + fallback) · kartica **🧑‍🎓 Kao učenik** | **50** (13 novih) | `UPDATE_25-10_fazaB_ekran_rjesavanja.md` |
| 25.10.2026. | **Faza A — temelj** | novi repo i aplikacija; `tablice`, `veza`, `model`, `banka`, `definicije`, `dodjele`, `provedba`, `ocjenjivanje`, `grupe`, `upute`, `app`; sigurnosna kočnica za živu bazu; popravci: gspread dict, pametni navodnici, `x=2` vs `2`, dvostruka predaja, miješanje odgovora, `__pycache__` | 37 (+94 stara) | `UPDATE_25-10_fazaA_temelj.md` |

---

## Kako dodati novi redak

1. Napravi `UPDATE_DD-MM_tema.md` po pravilu iz `00_PREGLED.md`.
2. Dodaj redak **na vrh** tablice (najnovije prvo).
3. Ažuriraj `ARHITEKTURA.md` ako se promijenio model podataka ili moduli.
4. U globalni `CAKI_razvoj/TRACKER.md` dodaj kratki unos (§5) — za koordinaciju s drugim agentima.
