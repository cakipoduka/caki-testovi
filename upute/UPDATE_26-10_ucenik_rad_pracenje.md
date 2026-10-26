# 📘 UPDATE 26.10.2026. — Ispravak: učenik sam prilaže rad + 👀 praćenje pristupa

**Status:** kod radi, **112 testova prolazi** · čeka commit + push + Reboot

---

## 1. Ispravak modela (Cakijeva napomena 26.10.2026.)

**Prije (pogrešno shvaćeno):** profesor skenira rad i prilaže ga.
**Sada (kako stvarno jest):** učenik rješava **od doma**, sam fotografira/skenira papirni dio i
**pošalje ga kroz svoj portal**. Profesor samo **pregleda i potvrđuje**.

Zato je prilog premješten u **stranicu učenika** (`pages/1_Ucenik.py`):

- u kartici svakog testa → **📷 Priloži svoj rad (fotografija ili sken)**
- učenik može **poslati datoteku** (slika/PDF) ili **zalijepiti poveznicu** (npr. s mobitela)
- rad se veže na **pokusaj**, a u polju `prilozio` piše **šifra učenika** — zna se da je njegov
- rad je odmah uz test, ali **nije pregledan**; profesor ga potvrđuje u Rezultatima

## 2. Upload u Drive — `drive.py`

Ako je `RADOVI_FOLDER_ID` postavljen, datoteka ide u Drive i vraća se poveznica.
Pravila:

| Situacija | Što se dogodi |
|---|---|
| datoteka > 25 MB | jasna poruka „smanji fotografiju" |
| prazna datoteka | odbija se |
| Drive nije dostupan / nema prava | poruka + **učenik i dalje može poslati poveznicu** |
| `RADOVI_FOLDER_ID` nije postavljen | poruka, nema uploada, poveznica radi |

**Nikad se ne gubi rad** — poveznica je uvijek moguća.

## 3. 👀 Praćenje pristupa — `posjete.py`

Caki dodjeljuje testove i šalje informacije, ali nije znao **je li učenik uopće otvorio portal**.
Sada se bilježi:

| Radnja | Kada |
|---|---|
| `posjeta` | učenik se prijavio na portal |
| `test` | otvorio pojedini test |
| `rad` | priložio svoj rad |

**Ključna zaštita — Google kvota.** Google dopušta ~60 upisa u minuti. Zato se posjeta upisuje
**jednom po sesiji** (`biljeska_jednom` + zastavica u sesiji), a ne pri svakom osvježenju. Bez toga bi
učenik koji pritisne F5 deset puta potrošio kvotu cijele aplikacije.

Prikaz: 📊 Rezultati → **👀 Praćenje pristupa**: šifra · koliko posjeta · koliko testova otvorio ·
radova · **zadnji put**. Gruba oznaka naprave (mobitel/tablet/računalo) iz `User-Agent`.

## 4. Novi tabovi u CRM-u

| Tab | Zašto |
|---|---|
| **`Radovi`** | priloženi radovi (skenovi i poveznice) |
| **`Posjete`** | tko je kad otvorio portal (jedan redak = jedna radnja) |

Oba se stvaraju klikom na **⚙️ Postavke → 🔧 Pripremi tabove**.

## 5. Testovi (15 novih, ukupno 112)

`testovi/test_v2_posjete_drive.py`:

- posjeta se upisuje s velikim slovima šifre; **bez šifre se ne piše** (ne troši kvotu)
- nepoznata radnja postaje `posjeta` (ne ruši)
- sažetak po učeniku: posjete, testovi, radovi, **zadnji put**
- **`biljeska_jednom`**: drugi poziv u istoj sesiji **ne piše** (štiti kvotu)
- tab bez posjeta → prazno, bez rušenja
- naprava iz `User-Agent` (mobitel/tablet/računalo/prazno)
- učenik prilaže rad poveznicom i datotekom; `prilozio` = **šifra učenika**, `potvrdjeno` prazno
- rad bez pokušaja se odbija
- Drive: MIME tipovi, provjera veličine/prazne datoteke, **uspjeh**, **bez foldera**, **greška Drivea**

## 6. Što Caki treba napraviti

1. Commit + push (`pages/1_Ucenik.py`, `posjete.py`, `drive.py`, `radovi.py`, `tablice.py`, `app.py`, ovaj dokument)
2. **Secrets:** `RADOVI_FOLDER_ID` (već ga imaš) — folder mora biti **podijeljen s testnim servisnim računom** kao Editor
3. Reboot app
4. ⚙️ Postavke → 🔧 Pripremi tabove (stvara `Radovi` i `Posjete`)
5. Probaj kao učenik: 📷 priloži fotografiju → pa u Rezultatima ✅ potvrdi pregled

## 7. Napomena o privatnosti

Praćenje je namjerno **minimalno** (bez IP-a, bez lokacije, bez sadržaja ekrana): samo „kad" i „što je
otvorio". To je dovoljno za Cakijevo pitanje „prati li", a ne prelazi u nadzor.
