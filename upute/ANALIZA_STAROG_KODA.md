# 🔍 Usporedba: stari Test Builder (1578 redaka) ↔ `caki-testovi` v2

**Zašto ovaj dokument:** Caki je 26.10.2026. pitao *„jesi sve izmjene uvrstio i analizirao stari kod —
da se ne vraćamo nazad?"* Ovo je poštena matrica, bez uljepšavanja.

---

## 1. Što stari builder ima (izmjereno iz koda)

**Sekcije:** `1. Pretraga baze` · `2. Odabrani zadaci` · `3. Metapodaci i generiranje` · `Objavi kao online test`
**Widgeti:** 3 selectbox · 4 multiselect · 5 checkbox · 10 text_input · 13 button · 1 download_button

| Funkcija | Dokaz u starom kodu |
|---|---|
| Predlošci testova (spremi/učitaj odabir) | `predloz` 15× |
| **Kategorije vrednovanja UZV/RP/MK** | `kategorij` 86× |
| **Bloom razina** | `bloom` 10× |
| Prikaži ponuđene odgovore (po zadatku) | `prikazi_opcije` 8× |
| „Mamac" odgovor (ništa od navedenog) | `mamac` 15× |
| Redoslijed zadataka (↑ ↓ 🗑) | `pomakni` 3×, `ukloni` 2× |
| **PDF preko pdflatexa** | `pdflatex` + `main_test_template.tex` + `caki-style.sty` |
| Rješenja na kraju | `rjesenja` 34× |
| Biblioteka izvora (filter) | `bibliotek` 11× |
| Nacrt (draft) s automatskim spremanjem | `draft` 33× |
| Objava kao online test | sekcija + `testovi_online` |

---

## 2. Stanje u v2 — funkcija po funkcija

| # | Funkcija | v2 status | Gdje |
|---|---|---|---|
| 1 | Pretraga baze + filteri | 🟡 **logika gotova, UI ne** | `builder.filtriraj` (višestruki filteri, potpoglavlje, izvor) |
| 2 | Stranice 20/30/40 | 🟡 logika gotova | `builder.stranica` |
| 3 | Prikaz formule (ne LaTeX kod) | 🟡 logika gotova | `builder.pripremi_za_prikaz` |
| 4 | Prikaz slika u popisu | 🟡 modul gotov | `slike_zadataka.prikazi_sliku_zadatka` |
| 5 | Kategorije UZV/RP/MK + blokada zbroja | ✅ **gotovo (model + PDF + test)** | `tex_test.provjeri_kategorije` |
| 6 | PDF preko pdflatexa | ✅ **gotovo (preuzet pipeline)** | `tex_test.generiraj` + `tex/` |
| 7 | Rješenja na kraju | ✅ gotovo | `tex_test.izgradi_tex(ukljuci_rjesenja=True)` |
| 8 | Kraj testa po tipu dokumenta | ✅ gotovo | `tex_test.KRAJ_OZNAKA` |
| 9 | Zaglavlje po kategorijama | ✅ gotovo | `tex_test.izgradi_kategorije_redovi` |
| 10 | **Predlošci testova** | ❌ **nema** | treba tab `Predlosci` |
| 11 | **Bloom razina u editoru** | ❌ nema (model ima polje `bloom`) | — |
| 12 | **Prikaži ponuđene odgovore (per zadatak)** | ❌ nema | — |
| 13 | **Mamac odgovor** | ❌ nema (funkcija `dodaj_mamac` postoji u `izgradi_tex`, UI ne) | — |
| 14 | **Redoslijed ↑ ↓ 🗑** | ❌ nema | — |
| 15 | **Nacrt (auto-spremanje odabira)** | ❌ nema (v2 sprema **definiciju**, ne radni odabir) | — |
| 16 | **Objavi kao online test iz buildera** | ❌ nema (v2 ima 👥 Objavi, ali ne iz istog ekrana) | — |
| 17 | Biblioteka izvora u filtrima | ✅ logika | `builder.filtriraj(izvor=[...])` |

**Zbroj: 9 gotovo · 8 logika-gotova-UI-ne · 6 nedostaje.**

---

## 3. Zašto to još nije u aplikaciji

Kartica 🧪 Testovi u v2 još koristi **stari jednostavni odabir** (multiselect). Novi moduli
(`builder`, `tipovi`, `tex_test`) su **gotovi i testirani**, ali **nisu spojeni**. Zato:
- ništa od ovoga **ne može pokvariti** ono što sada radi (nije uključeno), ali
- Caki to **još ne vidi** u aplikaciji.

---

## 4. Poštena ocjena rizika (Cakijevo pitanje o temeljitosti)

**Što je pokriveno testovima (219):** sve čiste funkcije — filteri, stranice, escapiranje, kategorije,
provjere, ocjenjivanje po tipu, PDF sastavljanje (TeX string), izvještaj, analitika.

**Što NIJE pokriveno:** **sučelje** (Streamlit). Ima samo 6 „dimnih" testova da se stranice otvore.

**Četiri greške koje su se stvarno dogodile:**

| Greška | Tko ju je našao | Pouka |
|---|---|---|
| `st.stop()` unutar kartice ugasio cijelu stranicu | Caki (prazne Postavke) | UI se ne testira dovoljno |
| Krivo rekao „PDF ne postoji" | **Caki** | morao sam tražiti `pdflatex`, ne samo `reportlab` |
| `bodovi` vs `max_bodovi` | Caki (poruka u app) | provjeriti shemu na **stvarnim** podacima |
| Prazne kategorije u PDF-u | **Caki** | usporediti sa starim kodom **prije** pisanja |

**Zaključak:** logiku pišem temeljito (testovi), **sučelje prebrzo**. Tri od četiri greške našao je Caki —
to je signal koji treba uvažiti.

## 5. Novo pravilo rada (od sada)

1. **Jedna funkcija = jedan zahvat**: kod → test → Caki potvrdi → sljedeće.
2. **Prije svakog zahvata**: pročitati odgovarajući dio starog builderа i popuniti matricu (§2).
3. **Svaka nova kartica dobiva dimni test** (AppTest) prije nego se javi „gotovo".
4. **Nikad ne tvrditi „ne postoji"** dok se ne pretraži cijeli repo po **mehanizmu** (pdflatex, API, worker), ne samo po biblioteci.

---

## 6. PDF kompajliranje — detaljna usporedba (Cakijev zahtjev 26.10.2026.)

Caki je upozorio da je Claude u PDF uložio puno rada na rubne slučajeve. Provjereno **funkcija po
funkcija**; nađene su **tri stvarne razlike** — jedna je rušila PDF.

| Zaštita u starom kodu | v2 prije | v2 sada |
|---|---|---|
| **`razdvoji_slike`** — više slika u polju, razdjelnik **`\|`** (npr. `a.png \| b.png`) | ❌ slao cijeli string kao jedno ime → *File not found* | ✅ **preuzeto** iz `baza_zadataka_pipeline.py` |
| **samo dohvaćene slike** idu u `\zadatakbod` (`if slike_bytes.get(x)`) | ❌ slao ime i kad slike nema → pdflatex padne | ✅ provjera prije slanja |
| **`broj_dolara`** — broji samo neescapirane `$` (`(?<!\\)\$`) | ❌ `count("$")` → lažna blokada na `\$` (cijena u tekstu) | ✅ **preuzeto** |
| `escape_outside_math` + `SPECIAL_CHARS` (\, &, %, #, _, {, }, ~, ^) | ✅ preuzeto | ✅ |
| `formatiraj_opciju` — čista matematika → `$…$`, običan tekst → escape | ✅ preuzeto | ✅ |
| `izgradi_opcije_blok` — prirodan tok, A) B) C), bilo koliko opcija | ✅ preuzeto | ✅ |
| `provjeri_zbroj_kategorija` (UZV/RP/MK) | ❌ bio prazan `{}` | ✅ preuzeto + blokada |
| dva prolaza `pdflatex`, `-no-shell-escape`, `-halt-on-error` | ✅ | ✅ (+ timeout 90 s) |
| log zadnjih 40 redaka pri padu | ✅ | ✅ (u `RuntimeError`) |
| `\cakiispithead` placeholderi (8) | ✅ | ✅ + provjera da nijedan nije ostao |
| `KRAJ_OZNAKA` po tipu dokumenta | ✅ | ✅ |
| `predmet_config` zaglavlje (MATEMATIKA/FIZIKA) | ⚠️ fiksno `MATEMATIKA` | ⚠️ isto — **za popraviti** |
| `izgradi_stavke_blok` (skupine a) b) c)) | ❌ **nema** u v2 | ❌ — v2 još ne podržava skupine |
| `prikazi_opcije` po zadatku (isključi opcije) | ❌ | ❌ |
| `dodaj_mamac` („ništa od navedenog") | ⚠️ funkcija postoji | ⚠️ nije u UI |
| `slika_valjana_za_prikaz` (provjera zaglavlja slike) | ❌ | ❌ — v2 šalje bajtove bez provjere |

**Zaključak:** jezgra PDF-a (escapiranje, opcije, kategorije, placeholderi, dva prolaza) **je preuzeta**,
ali tri zaštite oko **slika** i **dolara** su falile i sada su ugrađene.

### Što još treba prije nego PDF bude „kao stari"

1. **predmet_config** — zaglavlje po predmetu (sada fiksno `MATEMATIKA`).
2. **skupine zadataka** (a/b/c) — `izgradi_stavke_blok`, `izgradi_rjesenja_blok` (18 KB modul).
3. **`prikazi_opcije`** po zadatku.
4. **provjera zaglavlja slike** prije slanja u pdflatex.
