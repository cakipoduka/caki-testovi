# 🧪 CAKI testovi v2

**Nova generacija sustava testiranja.** Paralelni razvoj — stara tri repoa (`caki-baza-zadataka`,
`caki-booking-termina`, `caki-upisi-crm-main`) **se ne diraju** i rade dalje.

Gradi se po `CAKI_razvoj/upute/MASTER_SUSTAV_TESTIRANJA.md` (v2.0).

> 📚 **Arhiva razvoja je u mapi `upute/` unutar ovog repoa** — izvještaji po isporuci, kratke upute,
> arhitektura i dnevnik. Počni od `upute/00_PREGLED.md`.

---

## Zašto postoji

U starom sustavu „test" nije bio zapis — bio je skup redaka po učenicima s istom oznakom `serija`.
Zato se učenik nije mogao dodati nakon objave, nije bilo pokušaja ni autosavea, a mjerenje kvalitete
zadatka nije bilo moguće.

Ovdje je test **zapis** (`Definicije_testova`), a kome je poslan je **dodjela** (`Dodjele`). Dodavanje
učenika je zato nova dodjela — i duplikat više nije moguć.

## Što radi sada (Faza A)

| Kartica | Što |
|---|---|
| **🧪 Testovi** | popis testova + slaganje novog testa iz postojeće baze (filtri po cjelini/težini/tipu) |
| **👥 Objavi** | grupa / kanta / pojedinac, dopuna nakon objave, rok po učeniku |
| **📊 Rezultati** | po testu: rang, prosjek, raspon, **ko nije predao**, po grupama |
| **📈 Kvaliteta** | mjerenje zadataka: p, diskriminacija, distraktori, Cronbach α |
| **🧑‍🎓 Kao učenik** | pregled ekrana rješavanja (ništa se ne sprema) |
| **⚙️ Postavke** | provjera sustava/baze/tajni, Student View, priprema tabova |
| **📝 Ucenik** *(u bočnoj traci)* | **prava stranica učenika** — prijava šifrom, rješavanje, pregled |

**Još ne radi (sljedeće faze):** ekran rješavanja za učenika, autosave, mjerenje kvalitete zadatka
(p, r, distraktori), papir + skenovi.

## Kako se pokreće

### 1. Novi GitHub repo

Ova mapa je samostalna aplikacija. Napravi repo `caki-testovi` (privatan) i pushaj sadržaj mape.

> Prema `AGENTS.md` agent ne radi `git commit`/`push` — zato: ti napraviš repo, ja pripremam datoteke.

### 2. Nova Streamlit aplikacija

- **Main file path:** `app.py`
- **Secrets:**

```toml
APP_PASSWORD = "tvoja-lozinka"

# Za upis u CRM preporučen je ZASEBAN testni račun (odvaja Google kvotu od portala).
# Ako ga nemaš, dovoljan je i dijeljeni `GOOGLE_SERVICE_ACCOUNT_JSON`.
GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI = '''
{ ... JSON testnog servisnog računa ... }
'''
GOOGLE_SERVICE_ACCOUNT_JSON = '''
{ ... JSON dijeljenog servisnog računa ... }
'''

SHEET_ID = "ID baze zadataka (caki-baza-zadataka)"
CRM_SHEET_ID = "ID Sheeta CAKI CRM — Prijave i baza"
```

Redoslijed kojim se tajne traže (v. `veza.py`):

| Sheet | Prvo | Ako nema |
|---|---|---|
| CRM (upis testova) | `GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI` | `GOOGLE_SERVICE_ACCOUNT_JSON` |
| Baza zadataka (čitanje) | `GOOGLE_SERVICE_ACCOUNT_JSON` | `GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI` |

> **Poznata greška (popravljena 25.10.):** `gspread.authorize()` prima *credentials objekt*, a ne
> dict — zato se koristi `gspread.service_account_from_dict()`. Simptom je bio
> `'dict' object has no attribute 'module'`.

Servisni račun treba **Editor** na oba Sheeta (CRM za upis testova, baza samo čitanje).

### 3. Prvi put u aplikaciji

Kartica **⚙️ Postavke** → gumb **🔧 Pripremi tabove (prvi put)** — napravi tabove
`Definicije_testova`, `Dodjele`, `Pokusaji`, `Ocjene_zadataka`, `Statistika_zadataka`, `Dnevnik_radnji`
i doda stupce `video_url`/`video_naslov` u bazu zadataka.

## Struktura

| Modul | Što radi |
|---|---|
| `tablice.py` | **jedini sloj koji zna gdje podaci žive** (Sheets danas → Supabase kasnije) |
| `veza.py` | otvara Sheetove (vjerodajnice na jednom mjestu) |
| `model.py` | pretvorbe (datum, broj, JSON), ID-evi, vrijeme |
| `banka.py` | čita postojeću bazu zadataka, dodaje video, filtrira |
| `definicije.py` | test kao zapis: zadaci, Student View, A/B miješanje, provjere |
| `dodjele.py` | kome je test poslan, rok po učeniku, dopuna bez duplikata |
| `provedba.py` | pokušaj, autosave, predaja, ručna ocjena |
| `ocjenjivanje.py` | tri sloja: string → SymPy → AI (**AI samo predlaže**) |
| `grupe.py` | grupe Upisa i kante Mature |
| `rjesavanje.py` · `ekran_ucenika.py` | logika i ekran rješavanja (autosave, pregled) |
| `unos_odgovora.py` | matematičko polje (MathLive) + fallback |
| `slike_zadataka.py` · `drive.py` | slike zadataka i upload skenova (Drive) |
| `ai_pomoc.py` | 💡 pomoć (nikad rješenje, max 3 pitanja) |
| `analitika.py` | mjerenje zadataka (p, r, distraktori, α, po cjelinama) |
| `zakljucna.py` | 🎓 zaključna ocjena iz više testova |
| `izvjestaj.py` | 📄 izvještaj za roditelje (HTML → PDF) |
| `podsjetnik.py` | 📨 koga podsjetiti + tekst poruke |
| `posjete.py` | 👀 praćenje pristupa (jednom po sesiji) |
| `upute.py` | upute unutar aplikacije (nikad zasebna stranica) |

**Pravilo:** nijedan modul osim `tablice.py` ne uvozi `gspread`. Kad dođe Supabase, mijenja se jedan
modul.

## Testovi

Aplikacija ima testove u `../testovi/` (izvan ovog repoa, Cakijeva mapa):

- `test_v2_temelj.py` — 28 testova: model, tablice, definicije, dodjele (uključivo Cakijev bug),
  ocjenjivanje (string/SymPy/AI), provedba (autosave, dvostruka predaja, istek roka), banka + video
- `test_v2_app_apptest.py` — 3 dimna testa aplikacije (bez Googlea)

## Sljedeće (po MASTER dokumentu)

**Faza B:** ekran rješavanja za učenika (pitanje po pitanju, autosave, matematički unos, slike,
formule, 💡 pomoć, 🎬 video nakon testa) + „kako ovo vidi učenik" u ovoj aplikaciji.

---

## ⚠️ Ovo radi na ŽIVOJ bazi (CRM)

Aplikacija čita i piše u **pravi CRM Sheet**. Zato u kodu postoje dvije kočnice:

1. **Upis je zadano ISKLJUČEN** (`tablice.PISANJE = False`). Dok je tako, sve funkcije pisanja bacaju
   `PermissionError`, a aplikacija samo čita. Uključuje se u **bočnoj traci** („🔐 Živa baza") ili
   secretom `V2_UPIS = "da"`.
2. **Baza zadataka se NE mijenja.** Sustav iz nje samo čita. Ništa se ne dodaje u tab `Zadaci`.

**Priprema tabova** stvara isključivo **nove** tabove (`Definicije_testova`, `Dodjele`, `Pokusaji`,
`Ocjene_zadataka`, `Statistika_zadataka`, `Dnevnik_radnji`) i traži izričitu potvrdu. Ako tabovi već
postoje, ne mijenja ih.

## 🎬 Video rješenja — već u bazi

Cakijeva napomena (25.10.2026.): **video rješenja su planirana u bazi zadataka** — stupac `video_url`
postoji u shemi `Zadaci` (samo još nisu snimljena). Zato:

- sustav `video_url` **čita** kao i svaki drugi podatak zadatka;
- učenik ga vidi **nakon testa**, kad pregled rješenja postane dostupan (Student View);
- sustav **ne dodaje** stupce u bazu — ako stupca nema, to se samo prijavi Cakiju.

Novi sustav **ne treba** `video_naslov`: naslov se može izvesti iz cjeline/potpoglavlja zadatka.
(a `video_naslov` se koristi samo ako ga baza jednog dana dobije — kod je spreman i za to.)
