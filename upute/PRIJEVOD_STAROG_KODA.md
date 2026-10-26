# 🔬 PRIJEVOD STAROG KODA — detaljna analiza po domenama

Cilj: **ništa ne pisati iznova ako postoji**. Za svaku domenu: gdje je stari kod, koja je njegova
logika (doslovno), i je li preuzet.

---

## 1. Ponuđeni odgovori (A/B/C/D) — *aktivna greška 26.10.*

### Kako to radi u starom kodu

| Korak | Funkcija | Datoteka / linija | Logika |
|---|---|---|---|
| 1. zapis u bazi | specifikacija | `baza_zadataka_pipeline.py` (točka 13) | `ponudjeni_odgovori` = **JSON lista bez oznaka A/B/C/D**, redoslijedom kako se prikazuju |
| 2. prikaz u UI-u | **`prikazi_opcije_markdown(ponudjeni_odgovori)`** | `baza_zadataka_pipeline.py` | svaka opcija: ako sadrži `$` → ostavi; ako „izgleda kao rečenica" → običan tekst; inače → omotaj u `$…$` (matematika) |
| 3. prikaz u PDF-u | **`formatiraj_opciju`** + `izgradi_opcije_blok` | `2_test_builder.py` L1230/L1254 | čista matematika → `$…$` **bez** escapiranja; običan tekst → `escape_outside_math` (inače „trostranapiramida") |

### Što je v2 imao (greška)

- prikaz je sastavljao **sam** (`**A)** …` + `builder.pripremi_za_prikaz`) — nije koristio korak 2,
- parser je pokrivao samo JSON i `;` → drugi oblici = **prazno** → opcije se ne vide, a tip padne na
  `kratki_odgovor`.

### Sada

- **`banka.prikazi_opcije_markdown`** — **preuzeto doslovno** iz pipelinea (+ pomoćne funkcije),
- `banka._opcije` prihvaća: JSON, Python listu, `;`, `|`, prijelome, „A) …” (provjereno svih 5),
- `banka.opcije_markdown(zadatak)` koristi se u popisu → **isti prikaz kao u bazi**,
- PDF i dalje koristi `formatiraj_opciju`/`izgradi_opcije_blok` (preuzeto prije).

---

## 2. Slike — domena s najviše „naučenih" grešaka

| Lekcija | Datum | Stari kod | v2 |
|---|---|---|---|
| `st.image()` ruši proces (dekodiranje na serveru) | 15.9., 14.10. | `prikazi_sliku_html` (base64 `<img>`) | ✅ preuzeto |
| neispravna slika / krivo zaglavlje | — | `slika_valjana_za_prikaz` | ✅ |
| više slika u polju, razdjelnik `\|` | — | `razdvoji_slike` | ✅ |
| slika koja nije dohvaćena ruši pdflatex | — | u PDF ide samo `if slike_bytes.get(x)` | ✅ |
| 100+ zadataka sa slikama = sporo | 22.10. | ciljano učitavanje | ✅ toggle |

---

## 3. PDF (pdflatex)

| Dio | Stari kod | v2 |
|---|---|---|
| predložak + stil | `main_test_template.tex`, `caki-style.sty` | ✅ kopirano |
| 8 placeholdera | `.replace(...)` u L1470–1485 | ✅ + provjera da nijedan nije ostao |
| dva prolaza | `for _ in range(2)` | ✅ |
| zastavice | `-no-shell-escape -interaction=nonstopmode -halt-on-error` | ✅ |
| log pri padu | zadnjih 40 redaka | ✅ u poruci |
| U+0307 | `_escape_plain_segment` → `$\dot{x}$` | ✅ + test |
| neuparen `$` | `broj_dolara` + `pronadji_neuparene_dolare` | ✅ |
| kategorije UZV/RP/MK | `provjeri_zbroj_kategorija` (blokira PDF) | ✅ |
| rješenja | sekcija na kraju | ✅ + `\newpage` |
| **skupine zadataka (a/b/c)** | `skupine_zadataka.py` + `izgradi_stavke_blok` | ❌ **nije** |
| **zaglavlje po predmetu** | `predmet_config` | ❌ fiksno `MATEMATIKA` |

---

## 4. Baza → zamrznuti zadatak

| Polje | Stupac u bazi | v2 |
|---|---|---|
| bodovi | **`max_bodovi`** (ne `bodovi`) | ✅ alias |
| izvor/zbirka | **`biblioteka_izvora`** | ✅ alias |
| tekst | `tekst_zadatka_latex` / `_mathjax` | ✅ alias |
| odgovor | `konacan_odgovor` | ✅ alias |
| tip | `tip_zadatka` | ✅ alias |
| slika | `slika_putanja` | ✅ |

---

## 5. Pravilo za dalje

1. **Prije pisanja**: pronađi funkciju u starom kodu (po imenu ili po ponašanju) i pročitaj je **cijelu**.
2. **Ako postoji** → preuzmi (AST izdvajanje ili kopija modula), ne prepisuj.
3. **Ako je stranica** → izdvoji funkcije.
4. **Test za svaku preuzetu funkciju** + regresijski test za svaku Cakijevu prijavu.
5. U izvještaju napiši **odakle je preuzeto** (datoteka + funkcija).
