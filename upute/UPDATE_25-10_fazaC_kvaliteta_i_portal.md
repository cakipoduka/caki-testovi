# 📘 UPDATE 25.10.2026. — Faza C (1. dio): mjerenje zadataka + stranica učenika

**Status:** kod radi, **85 testova prolazi** · čeka commit + push + Reboot
**Grana:** `main` (repo `caki-testovi`)

---

## 1. 📈 Mjerenje kvalitete zadatka — `analitika.py`

Ovo je stvar koja u starom sustavu **nije postojala**: znalo se koliko je bodova, ali ne **vrijedi li
zadatak**. Sad svaki zadatak dobije četiri brojke i jednu rečenicu.

| Brojka | Što znači | Prag |
|---|---|---|
| **p (težina)** | udio učenika koji je riješio točno | < 0,30 pretežak · > 0,90 prelagan |
| **r (diskriminacija)** | razlikuje li dobre od slabijih (point-biserial) | < 0,20 ne razlikuje · < 0 krivo označen odgovor |
| **distraktori** | koliko je puta koji ponuđeni odgovor odabran | 0 odabira = „mrtav" |
| **Cronbach α** | pouzdanost cijelog testa | ≥ 0,70 prihvatljivo |

Uz svaku brojku ide **preporuka na hrvatskom**, npr.:

> „Prelagan i ne razlikuje — koristi ga kao uvodni, ne za ocjenu."
> „Provjeri je li točan odgovor dobro označen — bolji učenici griješe."
> „2 ponuđena odgovora nitko nije odabrao — zamijeni ga vjerojatnijim."

**Zaštita od pogrešnih zaključaka:** ispod **10 predanih radova** izvještaj piše da su brojke
orijentacijske. Bez toga bi profesor „popravljao" ispravne zadatke na temelju 4 učenika.

**Nova kartica 📈 Kvaliteta** u aplikaciji: 4 brojke gore, upozorenja, tablica po zadatku, i
sklopivi prikaz distraktora s trakama.

## 2. 📝 Stranica učenika — `pages/1_Ucenik.py`

Prvi put postoji **prava stranica za učenika**, odvojena od administracije:

1. **Prijava šifrom** (npr. `AA1111`) — bez lozinke, jer učenik vidi samo **svoje** dodjele.
2. **Popis testova**: naziv, broj zadataka, bodovi, trajanje, rok.
3. Stanje po testu:
   - rok nije počeo / prošao → poruka, nema rješavanja
   - `u_tijeku` → **▶ Nastavi** (autosave čuva odgovore)
   - `predano` → **✅ rezultat** + **Pregledaj rješenja**
4. **Pregled rješenja poštuje Student View**: rješenja i 🎬 video samo kad ih profesor dopusti;
   inače piše „Rješenja će biti dostupna nakon isteka roka."

## 3. Testovi (18 novih, ukupno 85)

| Datoteka | Broj | Što pokriva |
|---|---|---|
| `test_v2_analitika.py` | 15 | p-vrijednost, r (uključivo **negativan** kad bolji griješe), distraktori i „mrtvi", oznake, preporuke, Cronbach α, mali uzorak, prazan izvještaj |
| `test_v2_stranica_ucenika.py` | 3 | prijava se prikazuje, radi i bez Secrets, greška veze je **uhvaćena** (ne pad) |

Podaci u testovima su mali i ručno provjerljivi (5 učenika: tri dobra, dva slaba).

## 4. Što je namjerno zaštićeno

| Zaštita | Zašto |
|---|---|
| **„manje od 10 predanih → orijentacijsko"** | sprječava mijenjanje zadataka na temelju šačice učenika |
| **r < 0 se imenuje, ne skriva** | najčešći stvarni uzrok je **krivo označen točan odgovor** u bazi |
| **mrtav distraktor se označi** | ponuđeni odgovor koji nitko ne bira ne radi svoj posao |
| **stranica učenika ne prikazuje rješenja prije roka** | inače bi prvi koji preda podijelio odgovore |
| **pokušaji koji čekaju provjeru se javljaju** | brojke su tada privremene i to mora pisati |

## 5. Što Caki treba napraviti

1. GitHub Desktop (`caki-testovi`) → **Commit** → **Push**
   (`analitika.py`, `pages/1_Ucenik.py`, `app.py`, `upute.py`, testovi su izvan gita)
2. Streamlit → **Reboot app**
3. Nova kartica **📈 Kvaliteta** (puna je kad ima predanih radova)
4. U bočnoj traci se pojavljuje **Ucenik** — to je stranica učenika

## 6. Sljedeće

| # | Što |
|---|---|
| 1 | **📷 unos radova** (skenovi, papir + ekran) |
| 2 | **PDF izvještaj** po učeniku (ocjena + pregled) |
| 3 | **mjerenje po cjelinama** (koja cjelina najviše pada) |
| 4 | **prava prijava** učenika (PIN) ako se pokaže potreba |

---

## 7. Dopuna (iste noći): po cjelinama + CSV izvoz

**Po cjelinama.** Uz ocjenu po zadatku, sustav sada zbraja i **po cjelinama** — koja cjelina najviše
pada. U sažetku se pojavi rečenica:

> Najslabija cjelina: **Funkcije** (25 % točnih na 2 zadataka).

To je ono što učeniku kaže „vježbaj ovo", a profesoru „ovo nije sjelo na satu". Tablica je u kartici
📈 Kvaliteta (cjelina · zadataka · odgovora · točnih · p · udio bodova).

**CSV izvoz.** U 📊 Rezultatima gumb **„⬇️ Preuzmi rezultate (CSV za Excel)"** — datoteka se otvara u
Excelu s hrvatskim znakovima (`utf-8-sig`, separator `;`).

**Testovi:** +4 (`test_v2_analitika_cjeline.py`) → **ukupno 89**, svi prolaze. Uz to **89 testova
starih sustava** prolazi (ništa nije dirano).
