# UPDATE 21.11.2026. — MathLive u kratkim odgovorima + slanje postupka u Drive

Cakijeva prijava (dvije greške u testu):

1. U zadacima kratkog odgovora učenici više ne vide matematički editor (MathLive).
2. Nakon završetka testa slanje slike/PDF-a ne uspijeva: „Fotografija trenutno nije poslana na
   Drive — rad će se ipak spremiti. Pošalji i poveznicu ispod…”.

---

## 1. MathLive — uzrok i popravak (`unos_odgovora.py`)

Paket `streamlit-mathlive==0.0.3` (iz `requirements.txt`) ima potpis
`mathfield(title, value, enable_edit, upright, mathml_preview, key)`. Kod ga je zvao s
`default_mode="math"` i `height=90`, a takvih argumenata nema. Python je zato bacio `TypeError`,
`except` ga je **tiho** uhvatio i učenik je svaki put dobio obično tekstualno polje. Provjereno:
`unexpected keyword argument 'default_mode'`.

Na istom mjestu bila je i druga, skrivena greška. Komponenta vraća **par** `[latex, mathml]`
(prije prvog upisa `[None, None]`), a kod je radio `str(rezultat)`. Čim bi editor proradio, u
bazu bi išao tekst `"[None, None]"`. Gore je još i to da bi povratak na već odgovoreno pitanje
**obrisao** odgovor.

Popravak:
* `_poziv_argumenti()` pogleda potpis funkcije i pošalje samo argumente koje ta verzija prima.
  Ako se paket jednom nadogradi, nastavlja raditi.
* `_latex_iz_rezultata()` uzima samo LaTeX. Za `None` (komponenta još nije ništa javila) vraća
  postojeći odgovor.
* Tekstualno polje ostaje rezerva ako komponenta stvarno pukne.

Provjereno u pravom Streamlitu (AppTest) sa stvarnim paketom: nema tekstualnog polja, MathLive se
prikazuje, a upisani `x=3` ostaje sačuvan.

## 2. Drive — uzrok i popravak (`drive.py`)

`SCOPES` je bio `drive.file`. Ta dozvola dopušta pisanje **samo u mape koje je aplikacija sama
stvorila**. Mapu `02_Radovi_ucenika` (na dijeljenom disku) napravio je Caki ručno, pa Google
odbija upis. Sada se koristi `https://www.googleapis.com/auth/drive`. Servisni račun i dalje vidi
samo ono što mu je podijeljeno.

Poruka o grešci prije je bila samo `HttpError`. Nova `opis_greske()` čita Googleov razlog i kaže
što treba napraviti:
* `notFound`: folder ID ili članstvo servisnog računa
* `storageQuotaExceeded`: mapa mora biti na dijeljenom disku
* `insufficientFilePermissions`: uloga Contributor ili jača

**Ručno provjeriti (Caki):** servisni račun iz `GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI` mora biti
**član** dijeljenog diska na kojem je `02_Radovi_ucenika`, s ulogom *Contributor* ili *Content
manager*. Osim toga, `RADOVI_FOLDER_ID` u Streamlit Secrets mora biti ID te mape
(`1gTF2EIKA27lwUB_v89mDqZXCfrtbc7UF`). Ako i nakon Pusha slanje ne radi, poruka će sada pisati
točan razlog.

## 3. ⚠️ Portal (Moj CAKI, `caki-booking-termina`) — NIJE popravljen

Točan tekst „Fotografija trenutno nije poslana na Drive — rad će se ipak spremiti…” **ne postoji
u `caki-testovi`**. Dolazi iz portala, a pristup toj mapi u ovom razgovoru nije odobren.
`unos_odgovora.py` je po vlastitom zaglavlju kopija portalovog `kratki_odgovor_unos.py`, pa ako
učenici test pišu kroz portal, **obje greške su i tamo**. Isti popravak treba prenijeti u CRM/portal
projekt:
1. `kratki_odgovor_unos.py` → zamijeniti sadržajem ovog `unos_odgovora.py` (drži se identično).
2. U portalovom kodu za upload u Drive → `drive.file` zamijeniti s `drive` i ispisivati razlog
   greške (`opis_greske`).

## 4. Testovi

Novo: `testovi/test_mathlive_i_drive.py`, **19 testova**.

Vraćen fixture `upis_dozvoljen` u `testovi/conftest.py`. HANDOVER od 20.11. kaže da je tamo, ali
na disku ga nije bilo, pa je 25 postojećih testova padalo već pri postavljanju.

```
cd caki-testovi
python -m pytest testovi/ -q        → 128 passed, 2 failed
```

**Dva pada su od prije i nisu dirana** (`test_brisanje_i_arhiva.py`):
`test_obrisi_sa_silom_brise_cijelu_kaskadu` (`assert 0 == 1`) i `test_obrisi_vise_mjesana_hrpa`
(`'pokušaja' in 'Test ne postoji.'`). UPDATE od 20.11. tvrdi „111 passed”, dakle kod brisanja na
disku ne odgovara onome što su ti testovi očekivali. To je otvoreno pitanje za sljedeći korak.

---

📌 COMMIT
* Repo: `caki-testovi` · grana `main` · mapa `CAKI_razvoj\caki-testovi`
* Datoteke: `unos_odgovora.py`, `drive.py`, `testovi/conftest.py`,
  `testovi/test_mathlive_i_drive.py`, `upute/UPDATE_21-11_mathlive_i_drive.md`
* Poruka: `Popravak: MathLive u kratkim odgovorima + upload postupka u Drive (scope, poruka greške)`
* Uživo tek nakon **Push** (GitHub Desktop) + **Reboot** na Streamlit Cloudu.
