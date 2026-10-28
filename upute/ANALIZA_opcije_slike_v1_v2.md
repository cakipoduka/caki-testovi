# 🖼️ „Opcije su slike" — analiza i plan za v2 (bez pisanja koda)

**Dogovor 28.10.2026.:** izmjenu **Test Buildera v1** (`caki-baza-zadataka/pages/2_test_builder.py`)
radi Claude/DeepSeek. **v2 ne dira v1** — v2 samo **preuzima logiku** kad bude gotova, da se ne piše
dvaput.

---

## 1. Dva oblika podataka (oba postoje u bazi)

| | **Oblik A** — URL u opcijama | **Oblik B** — placeholder + slike |
|---|---|---|
| `ponudjeni_odgovori` | `["https://cdn.mathpix.com/cropped/x-06.jpg?height=435", …]` | `["slika A", "slika B", "slika C", "slika D"]` |
| `slika_putanja` | prazno | `SLIKA_04.png \| SLIKA_05.png \| SLIKA_06.png \| SLIKA_07.png` |
| Primjer | `A2011_ljetni_007`, `A2012_ljetni_012` | izlaz D6 uvоza (`uvoz_foldera.py`) |
| **v2 sada** | ✅ `<img>` u UI-u, `\includegraphics` u PDF-u | ❌ tekst „slika A" + galerija slika |

## 2. Claudeova pravila (preuzeti doslovno, ne izmišljati)

1. **Heuristika:** ako **sve** neprazne opcije odgovaraju obrascu `slika A` / `slika B` … → to su
   slike-opcije (placeholder koje AI upisuje po pravilu D6).
2. **Mapiranje slika → opcije:**
   - `broj_slika == broj_opcija` → sve slike idu redom A, B, C, D (nijedna nije „slika pitanja");
   - `broj_slika == broj_opcija + 1` → **prva** slika je slika zadatka, ostale redom uz opcije.
3. **Sigurni fallback:** ako se brojevi ne poklapaju ili neka slika nedostaje → **tekst ostaje tekst**
   (nikad ne pogađati naslijepo).
4. **Ne diraj** AI prompt ni shemu Sheeta — D6 već ispravno sprema podatke; popravak je **samo prikaz**.

## 3. Što v2 treba kad v1 bude gotov (jedan zahvat, ~30 min)

| Korak | Gdje | Što |
|---|---|---|
| 1 | `banka.zadatak_iz_retka` | prepoznati oblik B i **popuniti `opcije` imenima slika** (`SLIKA_04.png`…), uz oznaku `opcije_su_slike=True` |
| 2 | `tex_test.izgradi_opcije_slike` | **već postoji** (radi za oblik A) — primiti imena slika isto kao URL-ove |
| 3 | `banka.opcije_markdown` | za oblik B prikazati slike preko postojećeg HTML puta |
| 4 | testovi | 6 slučajeva: čist tekst (netaknut), oblik A, oblik B točan broj, oblik B `+1`, neusklađen broj (fallback), regresija običnih zadataka |
| 5 | provjera baze | prije uključivanja: ima li zadataka s **više slika iz drugog razloga** (galerija) — da heuristika ne tumači krivo |

## 4. Što od Clauda tražiti da bude spremno za kopiranje

Da izmjenu napiše kao **čistu funkciju** (bez Streamlita i bez PreTeXt-a), npr.:

```python
def opcije_kao_slike(ponudjeni_odgovori, slike) -> tuple[list[str], bool]:
    """Vrati (opcije, jesu_li_slike). Ako nije sigurno — vrati (opcije, False)."""
```

Tada je port u v2 **kopija jedne funkcije** + njezini testovi, bez prepisivanja.

## 5. Rizik (isti koji je Claude naveo)

Heuristika mora tražiti **placeholder tekst**, ne „ima više slika" — inače zadatak s galerijom
(npr. 3 slike uz jedan tekstualni zadatak) može biti krivo protumačen. Zato je fallback obavezan.

## 6. Stanje v2 danas (provjereno izlazom koda)

- **Oblik A:** `\textbf{A)}~\includegraphics[height=1.6cm]{images/x-06.jpg}` ✅
- **Oblik B:** `\textbf{A)}~slika A` (tekst) ❌ — čeka v1 logiku.

> Ovaj dokument je „ugovor" između v1 i v2: kad v1 bude gotov, v2 preuzima **samo funkciju** (točka 4)
> i testove (točka 3, red 4). Ništa se ne piše iznova.
