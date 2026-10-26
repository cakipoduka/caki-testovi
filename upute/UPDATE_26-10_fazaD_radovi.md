# 📘 UPDATE 26.10.2026. — Faza D (1. dio): 📷 radovi na papiru

**Status:** kod radi, **97 testova prolazi** · čeka commit + push + Reboot
**Grana:** `main` (repo `caki-testovi`)

---

## 1. Zašto

Cakijeva odluka (24.10.2026.): **papir i ekran u istom testu** — učenik dio rješava na papiru, dio na
računalu. Bez ovoga sustav ne može pokriti pravi ispit.

## 2. Kako radi

1. Učenik rješava ekranski dio (ili preda samo papir).
2. Profesor **skenira ili fotografira** rad.
3. U 📊 Rezultatima, uz učenika, prilaže rad:
   - **poveznicom** (Drive, mobitel, skener) — uvijek radi, ili
   - uploadom (kad je Drive dostupan).
4. Rad stoji kao **„⏳ čeka pregled"**, profesor klikne **✅ Potvrdi pregled**.
5. Tek tada je rad zaveden kao pregledan — **ocjena se ne prepisuje**, pamti se tko je i kada potvrdio.

## 3. Zašto poveznica, a ne samo upload

Ako Drive ne dopusti upis (kvota, prava, veličina datoteke, prekid), profesor i dalje može zalijepiti
link na sken. **Nikad ne ostane bez načina da priloži rad** — to je pravilo koje štiti ispitni rok.

## 4. Što je u kodu

| Funkcija | Što radi |
|---|---|
| `dodaj_vezu(...)` | prilaže rad poveznicom; odbija prazan link i rad bez pokušaja |
| `dodaj_upload(...)` | prilaže sken (bilježi veličinu datoteke) |
| `za_pokusaj` / `za_ucenika` | dohvat rada; **ne ruši se** ako tab još ne postoji |
| `potvrdi(...)` | bilježi pregled (vrijeme + profesor + napomena) |
| `sef_datoteke(...)` | sigurno ime datoteke (kvačice → c/z/s, razmaci → `_`, najviše 80 znakova) |
| `stanje(...)` | „2 rad(a) — 1 čeka potvrdu" |

Novi tab u CRM-u: **`Radovi`** (`rad_id`, `pokusaj_id`, `ucenik_id`, `naziv`, `veza`, `izvor`,
`velicina_bajtova`, `prilozio`, `prilozeno`, `potvrdjeno`, `napomena`). Stvara se sam klikom na
„Pripremi tabove" ili prvim prilaganjem.

## 5. Testovi (8 novih, ukupno 97)

`testovi/test_v2_radovi.py`:

- rad se veže na pokušaj i učenika (šifra se normalizira u velika slova)
- prilaganje **bez poveznice** i **bez pokušaja** se odbija s jasnom porukom
- upload bilježi veličinu; prazna datoteka se odbija
- **potvrda pregleda** mijenja stanje iz „čeka" u „pregledano"
- tab `Radovi` kojeg još nema → prazan popis, **bez rušenja**
- sigurno ime datoteke (kvačice, velika slova, razmaci, preduga imena)

## 6. Što Caki treba napraviti

1. Commit + push (`radovi.py`, `tablice.py`, `app.py`, ovaj dokument)
2. Reboot app
3. Ako želiš da se tab napravi odmah: ⚙️ Postavke → 🔧 Pripremi tabove (stvara i `Radovi`)
4. Probaj: 📊 Rezultati → uz učenika → „📎 Priloži rad" (zalijepi bilo koji link)

## 7. Sljedeće

| # | Što |
|---|---|
| 1 | **upload skena izravno u Drive** (kad potvrdimo prava na folder `RADOVI_FOLDER_ID`) |
| 2 | **PDF izvještaj** po učeniku (ocjena + pregled + prilozi) |
| 3 | **Šifrarnik ocjena** (zaključna ocjena iz više testova) |
