# 🧮 G1 + AI — tablica usklađenosti prije koda

**Nalog:** Caki, 01.11.2026. — prije pisanja koda pokazati što se iz v1 **preuzima**, što **prilagođava**,
a što **odbacuje** i zašto. v2 se razvija po MASTER-u; doslovno prepisivanje nije dopušteno.

**Izvor:** `caki-baza-zadataka/provjera_odgovora.py` (550 redaka, 23 funkcije, samo stdlib).

---

## 1. Slojeviti algoritam (dogovoreno)

```
normalizuj/string  →  SymPy (simbolički)  →  numerička provjera  →  AI (samo ako nesigurno)  →  sumnja
        ↑                                                                            ↓
   izvor_ocjene = string                                              red čekanja profesora (G4)
```

- **AI nikad ne daje konačnu ocjenu** — predlaže, upisuje se `izvor_ocjene = ai` i `sigurnost`.
- **Parse padne → `sumnja`** (nikad 0).
- Svaka promjena ocjene ide u **`Izmjene_ocjena`** (već postoji).

---

## 2. Tablica: 23 funkcije v1 → v2

| v1 funkcija | Odluka | Zašto / što se mijenja |
|---|---|---|
| `normalizuj(tex)` | **PREUZETI (jezgra)** | čisti LaTeX omotače, `\left`, `\!`, razmake; jedini izvor istine za normalizaciju |
| `skini_omotace` / `_skini_jedan_omotac` | **PREUZETI** | `$…$`, `\(…\)`, `\[…\]` — potrebno prije SymPyja |
| `_tekst` | **PRILAGODITI** | zamijeniti v2 `model.tekst()` (jedan izvor istine) |
| `razdvoji_jedinicu` / `_je_mjerna` | **PREUZETI** | `5 cm` vs `5` — stvarni slučajevi iz mature |
| `_bez_varijable` | **PRILAGODITI** | koristiti SymPy `free_symbols` umjesto regexa |
| `_kao_broj` / `_vrijednost_izraza` / `brojevi` | **PREUZETI** | pretvorba `\frac78`, decimalni zarez, postotak |
| `_jednaki` | **PREUZETI** | tolerancija za brojeve |
| `_alt_kljucevi` | **PRILAGODITI** | v2: `konacan_odgovor` + `odgovori` (više točnih) + `praznine` |
| `_uporedi_jedan` / `uporedi` | **PREUZETI + DOPUNITI** | dodati SymPy `simplify(a-b)==0` kao prvi korak |
| `blizu` | **PREUZETI** | „skoro točno" → profesor |
| `sastavi_pitanje` | **PRILAGODITI** | v2 prompt: oba izraza + tekst; traži `ekvivalentno: true/false/nesigurno` |
| `_izvuci_json` | **PREUZETI** | robusno vađenje JSON-a iz AI odgovora |
| `ai_uporedi` | **PRILAGODITI** | v2 adapter: `ai_pomoc.pitaj(poruke, kljuc, tajna)`; injektabilan `pozovi` za testove |
| `napravi_pozivac(secrets, model, timeout)` | **ODBACITI** | v2 ne prosljeđuje `secrets` objekt u module; adapter se pravi u `ai_pomoc` |
| `_sigurno_razlicita_vrijednost` | **ODBACITI** | heuristika „vjerojatno različito" — zamjenjuje je numerička provjera + `sumnja` |
| `odluci` | **PRILAGODITI** | v2 ugovor: `{tocno, bodovi, max, izvor, sigurnost, zasto}` + treće stanje `sumnja` |
| `tocno` | **PRILAGODITI** | ostaje kao tanki omotač za starije pozive (`ekran_ucenika`) |

**Nove funkcije kojih u v1 nema** (dodaju se u v2):
`sympy_jednako`, `numericki_jednako`, `pitanje_za_ai`, `oznaci_sumnju`.

---

## 3. Gdje ide koji kod (arhitektura)

| Modul | Što | Pravilo |
|---|---|---|
| `provjera_odgovora.py` *(nov)* | normalizacija, jedinice, brojevi, SymPy, numerika — **čiste funkcije**, bez `st` i bez `secrets` | testira se bez Streamlita |
| `ocjenjivanje.py` | spaja slojeve: `string → sympy → numerika → ai`; vraća `sumnja` | `normalizuj()` **delegira** na novi modul |
| `ai_pomoc.py` | adapter `pozovi(uputa, pitanje)` → `pitaj(...)` | jedino mjesto koje zna za API |
| `provedba.predaj()` | `dopusti_ai` iz **💡 AI pomoć** zastavice testa | AI se ne poziva ako test nema pomoć |
| `tipovi.py` | `popuni_praznine`, `povezivanje` koriste **istu** normalizaciju | bez duplog ponašanja |

---

## 4. Što se dodaje u `packages.txt`

```
antlr4-python3-runtime==4.11.1
```
— potrebno za `sympy.parsing.latex.parse_latex`. Bez toga: fallback čišćenje pa `sympify` (90 % slučajeva).

---

## 5. Testovi (prije sučelja)

**A. Parovi koje mora riješiti SymPy:**

| Točno | Učenički odgovor | Očekivano |
|---|---|---|
| `\frac78` | `7/8` | ✅ |
| `(x+1)^{2}` | `x^{2}+2x+1` | ✅ |
| `\sqrt{8}` | `2\sqrt{2}` | ✅ |
| `\frac{1}{2}` | `0,5` | ✅ |
| `\mathrm{A}` | `A` | ✅ |
| `45\degree` | `45^\circ` | ✅ |

**B. Parovi koji NISU jednaki:** `x+1` vs `x-1` · `2x` vs `x^{2}` · `5 cm` vs `5`.

**C. Rubovi:** prazno polje (`sumnja`, ne 0) · dvije varijable · jednadžba (`2x=4` vs `x=2`) · nemoguć parse
(`\begin{tabular}` u odgovoru) · AI nedostupan (test prolazi, ocjena `sumnja`).

**D. Sigurnost:** `sympify` bez `eval`, timeout 2 s, ograničen rječnik simbola.

---

## 6. Kriteriji prihvaćanja (§9 iz UPDATE_01-11)

1. 13 redaka iz §1 prestaje padati.
2. AI se **stvarno** poziva (dokaz u logu) kad je 💡 uključen, a **ne** poziva kad je isključen.
3. Kad AI nije siguran → zadatak ide u **red čekanja**, učenik **ne dobiva 0**.
4. Ručna ispravka mijenja **ukupne bodove** (G5, već napravljeno) i ostavlja trag.

---

📌 **Kod kreće nakon Cakijeve potvrde ove tablice.**
