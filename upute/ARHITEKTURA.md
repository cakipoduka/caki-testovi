# 🧱 Arhitektura — `caki-testovi` v2

**Kratki pregled strukture.** Ažurirati kad se doda modul ili promijeni model podataka.

---

## 1. Pravila koja se ne krše

1. **Nijedan modul osim `tablice.py` i `veza.py` ne zna gdje su podaci.** Kad dođe Supabase, mijenja
   se `tablice.py` — ostalo ostaje isto.
2. **Živa baza:** upis je zadano isključen (`tablice.PISANJE = False`). Sve funkcije pisanja bacaju
   `PermissionError` dok se ne uključi.
3. **Baza zadataka se samo čita.** Nikad se ne dodaje stupac ni redak u tab `Zadaci`.
4. **Nema poslovne logike u `app.py`.** Aplikacija samo spaja module i crta; sve odluke su u modulima
   (zato su testirani bez Streamlita).
5. **Rezultat je dokaz.** Predani pokušaj se ne prepisuje; ručna ocjena mijenja `izvor_ocjene`, ne briše trag.

## 2. Moduli

| Modul | Odgovornost | Ovisi o |
|---|---|---|
| `app.py` | sučelje: kartice, prijava, prekidač upisa — **⚠️ 30.10.2026.: narasao na 1420 redaka, dio poslovne logike procurio unutra, v. §7** | svi |
| `builder.py` | slaganje testa: filtri, stranicanje, prikaz zadatka (LaTeX+slike), sažetak odabira | `model`, `banka` |
| `tipovi.py` | katalog **9 modernih tipova zadatka** + jedinstveno ocjenjivanje po tipu — **izgrađeno 26.10., 13 testova, ⚠️ još NIJE spojeno nigdje, v. §7** | `model`, `ocjenjivanje` |
| `tablice.py` | **jedini sloj za podatke** (Sheets danas → Supabase kasnije) | `model` |
| `veza.py` | otvara Sheetove, odabir servisnog računa | `secrets_json` |
| `secrets_json.py` | tolerantno čitanje JSON-a iz Secrets | — |
| `model.py` | pretvorbe (broj, datum, JSON), ID-evi, vrijeme | — |
| `banka.py` | čita bazu zadataka, mapira u zamrznuti zadatak, filtri, video | `model`, `tablice` |
| `definicije.py` | **test kao zapis**, Student View, A/B miješanje, provjere | `model`, `tablice` |
| `dodjele.py` | kome je test poslan, rok po učeniku, dopuna bez duplikata | `model`, `tablice`, `provedba` |
| `provedba.py` | pokušaj, **autosave**, predaja, ručna ocjena | `model`, `tablice`, `definicije`, `ocjenjivanje` |
| `ocjenjivanje.py` | tri sloja: string → SymPy → AI (samo predlaže) | `model` |
| `grupe.py` | grupe Upisa + kante Mature | `model`, `tablice` |
| `upute.py` | upute unutar aplikacije (nikad zasebna stranica) | — |
| `rjesavanje.py` | logika rješavanja: napredak, „što nedostaje", povratna informacija po Student View-u | `model`, `ocjenjivanje` |
| `ekran_ucenika.py` | ekran rješavanja (stvarni učenik ili **pregled** bez upisa) | `provedba`, `rjesavanje`, `unos_odgovora`, `banka` |
| `unos_odgovora.py` | matematičko polje (MathLive) + fallback na tekst | — |
| `slike_zadataka.py` | slika uz zadatak iz Drivea (bez novog paketa, keš u memoriji) | `google-auth`, `requests` |
| `ai_pomoc.py` | 💡 pomoć: pravila „bez rješenja", max 3 pitanja, DeepSeek/Anthropic | `model` |
| `analitika.py` | mjerenje kvalitete: p, diskriminativnost, distraktori, Cronbach α, preporuke | `model` |
| `pages/1_Ucenik.py` | **stranica učenika**: prijava šifrom, popis testova, rješavanje, pregled | svi |
| `radovi.py` | 📷 radovi na papiru: prilog učenika ili profesora, potvrda pregleda (tab `Radovi`) | `model`, `tablice` |
| `drive.py` | upload skena u Drive (25 MB limit, fallback na poveznicu) | `google-api-python-client` |
| `posjete.py` | 👀 praćenje pristupa: posjeta/test/rad, **jednom po sesiji** (kvota) | `model`, `tablice` |
| `zakljucna.py` | 🎓 zaključna ocjena: prosjek kroz testove, pragovi, izostanak ≠ nula | `model` |
| `izvjestaj.py` | 📄 HTML izvještaj za roditelje (escapirano, bez font-rizika) | `model`, `zakljucna` |
| `pdf_izvjestaj.py` | 📄 PDF izvještaj (Vera.ttf iz reportlaba — hrvatska slova) | `model`, `zakljucna`, `reportlab` |
| `podsjetnik.py` | 📨 koga podsjetiti (3 stanja) + tekst poruke | `model` |
| `ucenici.py` | 🔎 pretraga učenika u CRM-u + dodjela testa po učeniku (bez šifre) | `model`, `tablice` |
| `tabele.py` | 📊 tablični podaci u zadacima prikazani kao prava tablica | `model` |
| `prijevod.py` | 🌐 prijevod odabranih zadataka (online test i PDF), baza se ne mijenja | `model` |
| `predlosci.py` | 📁 predlošci testa i nacrt — isti format kao v1 | `model`, `tablice` |
| `brend.py` | 🎨 podaci tvrtke za izvještaje — jedino mjesto koje Caki uređuje | — |
| `samoprovjera.py` | 🩺 popis već riješenih problema, provjera u živoj verziji | `model` |
| `skupine.py` | skupine zadataka (uvod + a,b,c) — preuzeto iz v1 `skupine_zadataka.py` | `model` |
| `pdf_test.py` | 📄 PDF testa za ispis (zaglavlje, uputa, zadaci, slike) | `model`, `reportlab` |
| `tex_test.py` | 📄 PDF testa preko pdflatexa — isti pipeline kao v1 Test Builder | `model` |

## 3. Model podataka

```
Definicije_testova  1 ──── n  Dodjele  1 ──── n  Pokusaji  1 ──── n  Ocjene_zadataka
   (test)                   (kome)              (rješavanje)         (po zadatku → mjerenje)
                                                                           │
                                                              Statistika_zadataka (izračunato)
```

| Tablica | Jedan redak = | Ključna polja |
|---|---|---|
| `Definicije_testova` | jedan test | `definicija_id`, `zadaci_json`, `status`, `student_view_json`, `varijanta_pravilo` |
| `Dodjele` | jedan učenik × jedan test | `dodjela_id`, `ucenik_id`, `grupa`, `rok_od/do`, `varijanta_seed` |
| `Pokusaji` | jedan pokušaj rješavanja | `pokusaj_id`, `pocetak`, `odgovori_json`, `bodovi`, `status` |
| `Ocjene_zadataka` | jedan zadatak u pokušaju | `tocno`, `bodovi`, **`izvor_ocjene`**, `vrijeme_s` |
| `Statistika_zadataka` | zadatak × test (izračunato) | `p_value`, `diskriminativnost`, `distraktori_json` |
| `Dnevnik_radnji` | jedna radnja | `kad`, `korisnik`, `radnja`, `sto` |

**Stanja testa:** `nacrt` → `objavljen` → `zatvoren` → `arhiviran`.
**Stanja pokušaja:** `u_tijeku` → `predano` / `po_isteku`.

## 4. Student View (odluka: po testu)

6 resursa × 3 stanja (`nikad` / `pri_predaji` / `uvijek`):

`bodovi` · `rjesenja` · `video` · `komentari` · `rezultat` · `pdf`

> Za `rjesenja` i `video`, `pri_predaji` znači **nakon isteka roka** — učenik koji prvi preda ne smije
> podijeliti odgovore. To je ugrađeno u `definicije.smije_vidjeti()`.

## 5. Ocjenjivanje — tri sloja i trag

| Sloj | Što rješava | `izvor_ocjene` |
|---|---|---|
| 1. string | normalizacija: razmaci, zarez/točka, jedinice, `x=2` vs `2` | `string` |
| 2. SymPy | ekvivalentni izrazi, razlomci, jednadžbe (usporedba rješenja) | `sympy` |
| 3. AI | prijedlog + obrazloženje, **samo kad je sigurnost „visoka"** | `ai` |
| — | kad nije sigurno → čeka profesora | `?` → `profesor` |

Zato svaki rezultat ima **trag kako je ocijenjen** (GDPR čl. 22: pravo na ljudsku provjeru).

## 6. Zašto ovako (ukratko)

| Problem u starom sustavu | Rješenje u v2 |
|---|---|
| „test" ne postoji, samo N redaka s istom `serija` | `Definicije_testova` |
| učenik se ne može dodati nakon objave | `Dodjele` — nova dodjela, duplikat se odbija |
| nema pokušaja ni autosavea | `Pokusaji` + `spremi()` |
| nema mjerenja kvalitete zadatka | `Ocjene_zadataka` → `Statistika_zadataka` |
| prekid = izgubljeni odgovori | autosave na svaku promjenu |


## 7. Poznati strukturni dug prije glavnog prelaska (30.10.2026., Claude)

Pregled stvarnog koda (ne samo ovog dokumenta) prije odluke o prelasku na `caki-testovi` kao
primarni sustav. Temelji (§1 pravila, poglavito #1 i #2) drže — provjereno: nijedan modul osim
`tablice.py`/`veza.py` ne uvozi `gspread`. Tri konkretne stvari treba riješiti rano u prelasku:

1. **`app.py` je prerastao pravilo #4** ("nema poslovne logike u app.py"). Tab 🧪 PDF (385 redaka)
   sadrži panel odabranih zadataka (dodaj/ukloni/pomakni ↑↓) izravno u `app.py`, bez testova —
   treba u `builder.py`. Tab 👥 Objavi sadrži "kome objavljujem" logiku kopiranu izravno iz v1
   (`caki-baza-zadataka/testovi_online.py`) — treba u `dodjele.py`, čiji je to opisani posao.
2. **`tipovi.py` postoji, testiran je (13/13), ali ga ništa ne koristi.** `ocjenjivanje.py`,
   `ekran_ucenika.py` i `definicije.py` i dalje provjeravaju samo `if tip == "visestruki_izbor"`
   umjesto da zovu `tipovi.ocjeni()`/`tipovi.polja()`. Spajanje je jeftino (1-2 dana) jer je
   registar već napisan — samo tri mjesta treba promijeniti da ga pozovu.
3. Ovaj dokument (modul-tablica) nije bio ažuriran uz 10 novih modula dodanih 28.-30.10. — pravilo
   iz vrha dokumenta ("ažurirati kad se doda modul") nije se poštovalo pod pritiskom brzine.
   Ažurirano ovim pregledom; **nastaviti ažurirati uz svaki novi modul od sada**, posebno jer ovo
   postaje primarni sustav.
