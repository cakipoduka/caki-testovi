# UPDATE 20.11.2026. — brisanje testova (rezultati DA/NE) + arhiva s više testova

Nastavak iste večeri, nakon `UPDATE_20-11_uredivanje_i_arhiva.md`. Cakijev zahtjev:
**„dodati opciju OBRIŠI TESTOVE iz arhive i baze (opcija obriši i rezultate DA/NE)".**

Cakijeve odluke uz ovu isporuku:

* arhiviranje **ostaje povratno** (potvrđeno — `vrati_iz_arhive` se ne vadi),
* „rezultati: NE" za test **s** pokušajima znači **odbijeno + predloži arhivu** (ne stvaramo siročiće),
* **testovi od sada idu u repo**, u `caki-testovi/testovi/`.

---

## 0. ⚠️ Jedan ručni korak prije pokretanja testova

Obriši **`CAKI_razvoj/testovi/test_definicije_uredivanje.py`** — datoteka je preseljena u repo
(`caki-testovi/testovi/`), a dvije kopije istog imena ruše pytest pri skupljanju:

```
import file mismatch: imported module 'test_definicije_uredivanje' has this __file__ ...
```

Claude ne smije brisati s diska, pa to ostaje tebi. Dok to ne obrišeš, `python -m pytest -q` iz
`CAKI_razvoj` prekida s greškom; iz mape `caki-testovi` radi normalno.

---

## 1. Zašto brisanje dosad nije radilo

Brisanje je **u modulu postojalo i radilo** (`definicije.obrisi(..., sila=...)`), ali u `app.py`
nije bilo dostupno. Oba su gumba stajala **unutar `except` blokova**:

| Red (prije) | Gumb | Gdje je zapravo bio |
|---|---|---|
| 916–917 | `🗑️ Obriši test (trajno)` | u tijelu `except` kartice **🧪 PDF** |
| 991 | `🗑️ Obriši test i SVE rezultate` | u tijelu `except` bloka **Ponovi test** |

Prikazali bi se samo da nešto drugo padne — a i tada bi pali, jer oba koriste `_odabir_l`, koji se
postavlja **isključivo u kartici 🧪 Testovi**, a oba su expandera bila u kartici 🧱 Složi test.

Oba su uklonjena i zamijenjena **jednim dijalogom u kartici 🧪 Testovi**, uz Kloniraj i Arhiviraj.

## 2. Tri defekta nađena pri provjeri (`_obrisi_s_rezultatima`)

| # | Što je bilo | Posljedica | Sada |
|---|---|---|---|
| 1 | uvjet je tražio stupac `statistika_id` | `Statistika_zadataka` se **nikad** nije brisala → siročići | briše se po `definicija_id` |
| 2 | `Pokusaji` su se brisali po `definicija_id` | taj stupac smije biti prazan (zato `pokusaji_testa()` traži preko `dodjela_id`) → pokušaj se promaši | briše se po `pokusaj_id` |
| 3 | dnevnik se pisao ključevima `radnja_id`/`kada`/`tko`/`detalji` | tab ima `kad`/`korisnik`/`radnja`/`sto`/`detalj` → **najrazornija radnja ostavljala je prazan redak** | ide kroz `tablice.zapisi_radnju()` |

Uz to je uklonjen mrtvi kod (`... if False else 0`).

## 3. Četvrti slučaj — našao ga je novi strukturni test

Test `test_nijedna_funkcionalnost_nije_zakopana_u_except_bloku` prošao je kroz cijeli `app.py`
i našao **treću pojavu istog obrasca**: cijela **`🧮 Matrica razreda — svi učenici × testovi`**
(38 redaka) bila je uvučena 4 razmaka previše i time upala u `except` blok Provjere odgovora —
vidjela se samo kad bi Provjera pala. Vraćena je na razinu susjednih blokova.

Pravilo koje test čuva: sučelje u `except` smije biti **samo objašnjenje greške** — bez gumba i
polja, do osam redaka. Zato „Što provjeriti" nakon neuspjele objave smije ostati (i jedan test
namjerno provjerava da pravilo nije previše strogo).

## 4. Nova kvota-zaštita: `tablice.obrisi_gdje()`

`tablice.obrisi()` briše **jedan** redak i pri svakom pozivu iznova čita cijeli tab. Test s 24
zadatka i 12 pokušaja ima 288 redaka samo u `Ocjene_zadataka` → red-po-red je 288 čitanja i 288
brisanja, dakle zajamčena greška **429 („kvota")** i test obrisan dopola.

`obrisi_gdje(sheet, tab, uvjeti)` čita tab **jednom** i briše susjedne retke **u bloku**. Prima
rječnik uvjeta jer `Ocjene_zadataka` i `Statistika_zadataka` nemaju jedinstven stupac. Ako tab ne
poznaje traženi stupac, **ne briše ništa** — radije ništa nego pogrešan redak.

## 5. Što je novo u kodu

**`tablice.py`** — `obrisi_gdje(sheet, tab, uvjeti) -> int`.

**`definicije.py`**
* `opseg_brisanja(sheet, definicija_id) -> dict` — brojevi za dijalog **prije** klika
  (`pokusaji`, `ocjene`, `dodjele`, `izmjene`, `zalbe`, `statistika`, `rezultata_ukupno`) plus
  `smije_bez_rezultata` i `razlog`. Read-only.
* `obrisi_vise(sheet, oznake, sila=False)` i `vrati_vise_iz_arhive(sheet, oznake)` — više testova
  odjednom; **jedan odbijeni ne zaustavlja ostale**, vraća se `{obrisani/vraceni, odbijeni, poruka}`.
* `_obrisi_s_rezultatima()` prepisan (§2), `obrisi()` sada briše dodjele jednim pozivom.

**`app.py`** — kartica 🧪 Testovi:
* **`🗑️ Obriši test`** — odluka `NE / DA` → tablica „što se briše" s pravim brojevima → potvrda.
  Uz DA traži se upis točnog ID-a. Zaključan gumb **uvijek piše zašto** je zaključan.
* **`🗄️ Arhiva — više testova odjednom (N)`** — pokazuje se kad je uključen prekidač
  🗄️ *Prikaži i arhivirane*. Višestruki odabir → `↩️ Vrati odabrane (N)` ili
  `🗑️ Obriši odabrane (N)`; za brisanje se upisuje riječ **OBRIŠI**. Prije klika piše koliko
  odabranih ima pokušaje i bit će odbijeno.

**`upute/ARHITEKTURA.md`** — dodana pravila 6 (testovi u repou) i 7 (sučelje ne stoji u `except`).

## 6. Testovi

Nova mapa **`caki-testovi/testovi/`** (u repou, Push ju čuva):

| Datoteka | Što |
|---|---|
| `conftest.py` | `sys.path` + **autouse fixture koji čisti `st.cache_data`/`cache_resource` i `tablice` keš** prije i poslije svakog testa (otvorena točka 2 iz handovera) i fixture `upis_dozvoljen` |
| `fake_gspread.py` | kopija; `delete_rows` sada prima i raspon `(r, end)` kao pravi gspread |
| `test_definicije_uredivanje.py` | preseljen iz `CAKI_razvoj/testovi/`, korijen je sada sam repo — **24 testa** |
| `test_brisanje_i_arhiva.py` | novo — **29 testova** |

**Ukupno 53 testa, svi prolaze**, i iz mape `caki-testovi` i iz `CAKI_razvoj`:

```
cd caki-testovi
python -m pytest testovi/ -q        → 53 passed
```

Svaki od tri defekta iz §2 ima svoj imenovani test koji bi na starom kodu pao
(`test_obrisi_sa_silom_brise_i_statistiku`, `..._brise_pokusaj_bez_definicija_id`,
`..._ostavlja_popunjen_trag`). Kvota je pokrivena s
`test_obrisi_gdje_susjedne_retke_brise_u_jednom_pozivu`.

**CRM testove** (`test_admin_app.py`, `test_portal.py`, `test_matura_dolasci.py`) nisam mogao
pokrenuti — oni testiraju `caki-upisi-crm`, koji nije bio u ovoj sesiji. Ne diraju `caki-testovi`.
Pokreni ih kod sebe nakon brisanja iz §0.

## 7. Što provjeriti kad digne (poslije Push + Reboot)

1. ⚙️ **Uključi upis** (ili `V2_UPIS = "da"`) — bez toga svako brisanje baca `PermissionError`.
2. 🧪 Testovi → odaberi **nacrt bez pokušaja** → `🗑️ Obriši test` → NE → tablica pokazuje samo
   `Definicije_testova` i `Dodjele_ispita` → obriši → nestane s popisa.
3. Odaberi test **s predanim pokušajima** → NE → gumb je zaključan i piše zašto, uz predloženu arhivu.
4. Isti test → DA → tablica pokazuje i pokušaje, ocjene, žalbe, statistiku → upiši ID → obriši.
5. ⚙️ Postavke → pogledaj `Dnevnik_radnji`: redak `obrisan_test_s_rezultatima` s **popunjenim**
   stupcima `kad`, `korisnik`, `sto`, `detalj`.
6. 🗄️ *Prikaži i arhivirane* → pojavi se **🗄️ Arhiva — više testova odjednom** → odaberi dva →
   `↩️ Vrati odabrane (2)` → status `zatvoren`.
7. 📊 Rezultati → **🧮 Matrica razreda** mora se vidjeti i kad Provjera odgovora radi normalno.

## 8. Ostaje (nije u ovom opsegu)

* Tvoja skica sučelja — raspored kartica po njoj; mockup novog ekrana je na platnu
  („CAKI Testovi v2 — sučelje 🧪 Testovi + brisanje").
* Uređivanje teksta pojedinog zadatka unutar slagalice.
* `UVOZ_FOLDER_ID` u Secrets (baza zadataka).
* `STATUS.md` još piše „Testovi: 143 prolazi" — broj je od 26.10. i nije osvježavan; nisam ga
  dirao jer ne znam koliko ih je u ostalim repoima.
* Preostali izgubljeni testovi faze A (baza zadataka) — drugi repo, drugi posao.

---

📌 **COMMIT:** mapa `caki-testovi` → repo `caki-testovi` → grana **main** → ✅ ide uživo nakon Push + Reboot
  · izmijenjeno: `tablice.py`, `definicije.py`, `app.py`, `upute/ARHITEKTURA.md`
  · novo: `testovi/conftest.py`, `testovi/fake_gspread.py`, `testovi/test_definicije_uredivanje.py`,
    `testovi/test_brisanje_i_arhiva.py`, `upute/UPDATE_20-11_brisanje_testova.md`

📌 **COMMIT:** mapa `CAKI_razvoj/testovi` → nije u gitu → nema commita;
  ručno obriši `test_definicije_uredivanje.py` (preseljen u repo, v. §0)
