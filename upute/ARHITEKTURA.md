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
| `app.py` | sučelje: 4 kartice, prijava, prekidač upisa | svi |
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
