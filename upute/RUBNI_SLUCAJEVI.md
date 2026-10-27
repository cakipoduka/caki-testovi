# ⚠️ Rubni slučajevi iz starog Test Buildera (verzija 1)

**Izvor:** svi komentari u `caki-baza-zadataka/pages/2_test_builder.py` koji nose naučeno
(30 zapisa). Za svaki: što je bio problem i je li u v2 pokriveno.

| Linija | Problem / odluka iz starog koda | v2 |
|---|---|---|
| L31 | Bloom razine — jedan izvor istine (isti popis kao sustav testova) | 🟡 u panelu odabranih (6 razina); nije u analizi |
| L37 | Skupine zadataka (uvod + stavke a), b), c)) — zaštićen import | ❌ NIJE preuzeto (`skupine_zadataka.py`, 18 KB) |
| L93 | Tip dokumenta (11.9.) — mijenja KRAJ OZNAKU i ponašanje | ✅ preuzeto (`TIP_DOKUMENTA`, `KRAJ_OZNAKA`) |
| L152 | Predmet — SVOJ Sheet i SVOJ folder slika | ❌ v2 ima jedan Sheet; zaglavlje PDF-a fiksno MATEMATIKA |
| L304 | Predlošci testova + autospremanje nacrta (14.9.) | ❌ NIJE preuzeto — najveća ušteda vremena |
| L392 | U+0307 rušio kompajliranje (17.9.) → pretvorba u `$\dot{x}$` | ✅ preuzeto + test |
| L512 | Klasifikacija (cjelina/potpoglavlje) zamrzava se u online test | ✅ v2 zamrzava cijeli zadatak u `zadaci_json` |
| L570 | Ponuda za učitavanje nacrta — provjerava se JEDNOM | ❌ nema (uz predloške) |
| L638 | Filter po `biblioteka_izvora` (10.10.) | ✅ preuzeto (`ALIASI['izvor']`) |
| L646 | 100+ zadataka sa slikama = sporo → ciljano učitavanje | ✅ toggle „Prikaži slike” |
| L653 | Jedinica = zadatak ILI skupina s stavkama | ❌ nema (skupine) |
| L677 | Cakijev nalaz „ne mogu naći logaritme iz udžbenika” — filter je nudio krive opcije | ✅ šifrarnik kao izvor potpoglavlja |
| L686 | Onemogući ponovno dodavanje istog zadatka | ✅ „✓ već dodano” |
| L695 | Paginacija umjesto tvrdog reza na prvih 30 | ✅ 20/30/40 + gore i dolje |
| L698 | Bug: filter po cjelini/potpoglavlju davao krive rezultate | ✅ šifrarnik + upozorenje na neusklađene |
| L717 | Masovno dodavanje „sve prikazane” | ✅ „Dodaj sve prikazane” |
| L792 | Sličica izravno u popisu | ✅ HTML/base64 slike |
| L937 | Redoslijed preko brojeva pozicija (15.9.) | ✅ ↑↓ u panelu |
| L979 | Bloom se označava SAMO za zadatke koji uđu u test | 🟡 u panelu (na odabranima) |
| L1010 | Kompaktan, UVIJEK vidljiv status zbroja kategorija | ✅ blokada + opis u PDF-u; 🟡 nema trajne trake u UI-u |
| L1076 | Zbroj kategorija: `int()` + `.isdigit()` TIHO pogrešan | ✅ `broj_iz_stringa` (decimalni zarez) |
| L1102 | Kategorizacija opcionalna po zadatku | ✅ provjera samo kad kategorije postoje |
| L1107 | Sve izvan kategorija — posljedica dizajna, ne bug | ℹ️ dokumentirati u uputama |

## Što od ovoga još NIJE u v2 (prioritet)

1. **Skupine zadataka (a/b/c)** — bez toga dio zadataka iz baze ne može u test.
2. **Predlošci testova + nacrt** — Cakiju najveća ušteda vremena.
3. **Predmet (Sheet + folder slika + zaglavlje PDF-a)** — sada jedan Sheet.
4. **Traka sa zbrojem kategorija u UI-u** — sada se vidi samo pri blokadi.

## Pravilo

Svaki novi rubni slučaj koji Caki prijavi → **dodaje se u `test_v2_regresije.py`** i u ovu
tablicu. Tako se treći put ne ponavlja.