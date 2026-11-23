# UPDATE 23.11.2026. — rješenja nakon zatvaranja, uklanjanje učenika, slanje rada

Cakijeva prijava (testni račun OH3229, kopija „Inicijalno testiranje - MATURA A razina (demo2)"):

1. Ispit je zatvoren, a učenik u Moj CAKI vidi „Rješenja će biti dostupna nakon isteka roka".
2. Zato ne može ni uputiti žalbu.
3. **OBAVEZNO:** uklanjanje pojedinog učenika s dodijeljenog ispita.
4. Slika poslana 4 puta, na Driveu je nema, a izvještaj za roditelje kaže „D..jpg — čeka pregled".

Portalov dio je u `caki-booking-termina/upute/UPDATE_23-11_rjesenja_zalbe_radovi.md`.

---

## 1. Zatvoren test = zatvoren rok (`dodjele.py`, `definicije.py`)

**Uzrok.** `stanje_roka()` gledao je samo datum. Učenik dodan nakon roka testa dobiva rok = dan
dodjele (Cakijeva odluka 2), dakle testni račun dodan 23.11. imao je rok do kraja 23.11.
„Zatvori odmah" je postavljao samo `rok_do = jučer` na testu, a dodjela ga je preglasala.
Rješenja (`pri_predaji`) se zato nisu otvorila.

**Popravak.**
* `stanje_roka()`: status `zatvoren` ili `arhiviran` uvijek znači `zatvoren`, bez obzira na datum.
  Isto pravilo zato vrijedi svugdje: rješenja, video, blokada novog početka rješavanja.
* `zatvori_odmah()` uz `rok_do = jučer` postavlja i `status = zatvoren`. Arhivirani test ostaje
  arhiviran.
* Objavljen test i dalje ovisi o datumu, kao i prije.

## 2. Uklanjanje učenika s testa (`dodjele.py`, kartica 👥 Objavi)

Nova funkcija `ukloni_ucenika(sheet, dodjela_id, s_rezultatom=False)`:
* učenik **bez pokušaja**: briše se samo dodjela;
* učenik **s pokušajem**: odbija se, osim uz izričitu potvrdu „obriši i njegov rezultat". Tada se
  brišu njegove ocjene, izmjene ocjena, žalbe i priloženi radovi, zatim pokušaj, pa dodjela.
  Pravilo je isto kao kod brisanja testa (20.11.): rezultat ne ostaje bez dodjele;
* ostali učenici, isti učenik na drugim testovima i sam test se ne diraju;
* trag ostaje u `Dnevnik_radnji` (`uklonjen_ucenik`).

Uz to `opseg_uklanjanja()` samo prebroji što bi se obrisalo, za upozorenje prije brisanja.

**Sučelje:** 👥 Objavi → odaberi test → „🧑‍🎓 Kome je test dodijeljen (N) — ukloni učenika".
Tablica prikazuje učenika, šifru, stanje (nije počeo / u tijeku / predao) i dodjelu. Učenika
biraš iz padajućeg izbornika. Ako ima rezultat, pokaže se broj ocjena, žalbi i radova, a gumb je
zaključan dok ne označiš potvrdu.

## 3. Slanje rada (`radovi.py`, `drive.py`, `pages/1_Interni_pregled.py`)

**Uzroci.**
* Kad Drive odbije sliku, rad se ipak zapisivao: redak s imenom datoteke, bez slike i bez
  poveznice (sama slika se nigdje ne čuva). Odatle „D..jpg — čeka pregled" bez ičega na Driveu.
* Poruka s razlogom ispisala se pa ju je `st.rerun()` odmah izbrisao. Razlog nitko nije vidio.
* Drive čita `GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI` **ako postoji**, a Sheet portala obični
  `GOOGLE_SERVICE_ACCOUNT_JSON`. Ako aplikacija ima oba ključa, to mogu biti dva različita računa.

**Popravak.**
* `radovi.posalji_ucenikov_rad()`: Drive primio, pa zapis s poveznicom. Drive odbio, ali ima
  poveznice, pa zapis poveznice, a razlog ide u `napomena`. Drive odbio bez poveznice, pa se
  **ništa ne zapisuje** i učenik dobije jasnu poruku.
* Poruka se čuva u `session_state` i ne nestaje. „Tehnički detalj (za Cakija)" sada sadrži
  razlog **i servisni račun** (`· račun: …@… (iz KLJUČ)`).
* `drive.opis_greske()` prepoznaje i „Google Drive API nije uključen u Cloud projektu"
  (`accessNotConfigured` / `SERVICE_DISABLED`), a nepoznatoj grešci dodaje Googleovu poruku.
* `drive.provjeri_pristup()` je dijagnostika bez upisa: vidi li račun mapu, smije li dodavati,
  je li mapa na dijeljenom disku. Gumb je u ⚙️ Postavke → „📁 Drive za radove učenika".

**Napomena:** to provjerava Secrets **ove** aplikacije. Moj CAKI ima svoje Secrets, pa njegov
razlog piše ispod poruke u portalu.

## Testovi

```
cd caki-testovi
python -m pytest testovi/ -q        → 158 passed, 2 failed
```
Novo: `test_zatvoren_i_uklanjanje.py` (14), `test_slanje_rada.py` (16). U
`test_mathlive_i_drive.py` je promijenjeno jedno očekivanje: poruka greške sada nosi i tekst.
Dva pada su od prije (`test_brisanje_i_arhiva.py`, v. UPDATE 21.11.) i nisu dirana.

---

📌 COMMIT
* Repo: `caki-testovi` · grana `main` · mapa `CAKI_razvoj\caki-testovi`
* Datoteke: `app.py`, `dodjele.py`, `definicije.py`, `drive.py`, `radovi.py`,
  `pages/1_Interni_pregled.py`, `testovi/test_zatvoren_i_uklanjanje.py`,
  `testovi/test_slanje_rada.py`, `testovi/test_mathlive_i_drive.py`,
  `upute/UPDATE_23-11_rjesenja_uklanjanje_radovi.md`
* Poruka: `Zatvoren test otvara rješenja; uklanjanje učenika s testa; slanje rada bez lažnog zapisa`
* Uživo tek nakon **Push** + **Reboot caki-testovi**.
