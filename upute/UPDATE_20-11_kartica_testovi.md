# UPDATE 20.11.2026. (treća isporuka) — kartica 🧪 Testovi po mockupu + zdravlje koda

Treća isporuka tog dana, nakon `UPDATE_20-11_uredivanje_i_arhiva.md` i
`UPDATE_20-11_brisanje_testova.md`. Caki je potvrdio da brisanje radi uživo i rekao da se
držimo mockupa „CAKI Testovi v2 — sučelje 🧪 Testovi + brisanje" (svoju skicu nije radio).

---

## 1. Novi raspored kartice 🧪 Testovi

Prije: tablica svih testova, pa `selectbox` ispod nje, pa radnje još niže. Odabrani test nije se
vidio u popisu, a radnje su bile dva zaslona daleko od onoga nad čim rade.

Sada, po mockupu — **popis lijevo, detalj desno**:

* **Lijevo:** traženje po nazivu ili ID-u, pa testovi kao kartice. Svaka nosi naziv, čip statusa,
  broj zadataka, bodove i rok. Odabrana je plavo obrubljena i njezin gumb piše „✓ Odabrano".
* **Desno:** zaglavlje s nazivom, oznakom, čipovima i tri broja (zadataka / bodova / pokušaja);
  ispod njega poruka o zaključavanju kad je potrebna; pa okvirni podaci (obrazac), „Što učenik
  vidi" i traka radnji.
* Dijalog brisanja i arhiva s više testova ostaju ispod, nedirnuti.

Statusi se više nigdje ne ispisuju sirovi: `zatvoren` → **Zatvoren** (UX pravilo 5).
Prazno stanje kaže što napraviti, a ne samo da je prazno (pravilo 6).

**Što mockup ne može dati u Streamlitu.** Mockup je HTML i CSS; Streamlit daje widgete. Vjerno su
ispali raspored u dva stupca, kartice, čipovi i brojevi. Razlika: odabir je gumb **unutar**
kartice, ne cijela kartica kao jedna velika meta, jer bi to tražilo nevidljiv gumb preko kartice —
a to Tab tipka preskače i čitač zaslona ne pročita.

## 2. Novi modul `tema_testovi.py`

`caki_tema.py` je po vlastitom opisu **ista datoteka u `caki-testovi`,
`caki-evidencija-dolazaka`, `caki-booking-termina` i CRM adminu**. Da se četiri kopije ne raziđu,
nove komponente stoje u zasebnoj datoteci koja se nadograđuje na nju:

```python
tema.primijeni()            # zajednička tema
tema_testovi.primijeni()    # dodatak samo za ovaj repo
```

Dodatak ne redefinira nijednu `--kc-*` varijablu zajedničke teme (to čuva test); uvodi samo
svoje `--tt-*`. Sve funkcije su čiste — grade HTML i escapiraju ono što dolazi od korisnika, pa
su testirane bez Streamlita.

## 3. Zdravlje koda: pet nedefiniranih naziva

Uz isporuku je puštena provjera `pyflakes` preko **cijelog repoa**. `app.py` je duga skripta koju
Streamlit izvodi od vrha prema dnu, pa krivo napisano ime varijable ne pukne dok netko ne otvori
baš taj blok. Nađeno pet slučajeva:

| Datoteka | Naziv | Što se događalo | Stanje |
|---|---|---|---|
| `app.py` (2×) | `_odabir_r` | varijabla se zove `odabir_r`; dva gumba **⬇ CSV** u kartici 📊 Rezultati rušila su svoj blok pri svakom crtanju | **popravljeno** |
| `pages/1_Interni_pregled.py` (2×) | `sifra` | nije u dosegu funkcije `_kartica()`; **učenikovo slanje fotografije rada rušilo se** | **popravljeno** — uzima se `dodjela.get("ucenik_id")`, kao u retku 120 iste datoteke |
| `uvoz_v1.py` | `_kao_tekst` | unutar `try/except`, pa je `_imena_iz_svih_tabova()` **tiho vraćao prazno** umjesto da nađe imena — gore od pada, jer se ne vidi | **popravljeno** — `model.tekst`, kako se zove na 145 drugih mjesta u istoj datoteci |
| `tex_test.py` | `sve_stavke_dolari_neuparene` | funkcija nigdje ne postoji; provjera neuparenih `$` u LaTeXu pada za zadatke sa `stavke` (skupine a, b, c) | **ostaje** — treba je napisati, nije posao za ovu isporuku |

Zadnji je upisan u `POZNATO` u testu, pa provjera čuva od **novih** slučajeva umjesto da stalno
crveni. Kad se popravi, test traži da se i s tog popisa obriše.

## 4. Testovi

| Datoteka | Testova | Što |
|---|---|---|
| `testovi/test_definicije_uredivanje.py` | 24 | uređivanje i arhiva (od ranije) |
| `testovi/test_brisanje_i_arhiva.py` | 30 | brisanje, kaskada, više testova; +2 nova za novi odabir i za jedan poziv `opseg_brisanja` |
| `testovi/test_tema_testovi.py` | 28 | **novo** — natpisi statusa, escapiranje HTML-a, raspored u `app.py` |
| `testovi/test_zdravlje_koda.py` | 3 | **novo** — pyflakes preko cijelog repoa |

**Ukupno 85 testova, svi prolaze:**

```
cd caki-testovi
python -m pytest testovi/ -q        → 85 passed
```

Novo i `requirements-dev.txt` (`pytest`, `pyflakes`) — alati za razvoj, koje Streamlit Cloud
nikad ne instalira jer čita samo `requirements.txt`:

```
pip install -r requirements.txt -r requirements-dev.txt
```

## 5. Što provjeriti kad digne (poslije Push + Reboot)

1. 🧪 Testovi → popis lijevo ima kartice, odabrana je plavo obrubljena, desno se odmah mijenja detalj.
2. Upiši dio naziva u „Traži" → popis se suzi; obriši pojam → vrate se svi.
3. Odaberi test **s pokušajima** → plava poruka „Zadaci su zaključani", a naziv i rok se i dalje mijenjaju.
4. Odaberi **arhivirani** test (uključi prekidač) → narančasta poruka i samo dvije radnje:
   ↩️ Vrati iz arhive i ✏️ Uredi sadržaj.
5. 📊 Rezultati → **⬇ CSV — uspjeh po zadatku** i **po cjelinama** sada se preuzimaju bez pada.
6. 📝 stranica Ucenik → 📷 Priloži svoj rad → slanje prolazi (prije je rušilo blok).
7. Provjeri da ekran radi i na užem prozoru — stupci se tada slažu jedan ispod drugoga.

## 6. Ostaje

* **Uređivanje Student Viewa** po testu. Mockup ga prikazuje, a u aplikaciji je zasad samo
  **prikaz** — `izmijeni()` ne dira `student_view_json` (nije u `META_POLJA`). Za uređivanje
  treba nova funkcija u `definicije.py` i njezini testovi; nije uneseno da se ne bi pisao
  neprovjeren put upisa.
* `tex_test.py` — napisati `sve_stavke_dolari_neuparene()` (§3).
* Uređivanje teksta pojedinog zadatka unutar slagalice.
* `STATUS.md` još piše „Testovi: 143 prolazi" — broj je od 26.10.

---

📌 **COMMIT:** mapa `caki-testovi` → repo `caki-testovi` → grana **main** → ✅ ide uživo nakon Push + Reboot
  · izmijenjeno: `app.py`, `definicije.py`, `uvoz_v1.py`, `pages/1_Interni_pregled.py`,
    `upute/ARHITEKTURA.md`, `testovi/test_brisanje_i_arhiva.py`
  · novo: `tema_testovi.py`, `requirements-dev.txt`, `testovi/test_tema_testovi.py`,
    `testovi/test_zdravlje_koda.py`, `upute/UPDATE_20-11_kartica_testovi.md`
