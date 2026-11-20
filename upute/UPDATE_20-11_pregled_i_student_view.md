# UPDATE 20.11.2026. (četvrta isporuka) — pregled riješenog testa + uređivanje Student Viewa

Dva ekrana s platna „CAKI nacrti", oba u repou `caki-testovi`. Cakijev zahtjev:

> „Nakon testa učenik bi trebao vidjeti ponovo zadatke s testa jer neće upamtiti svaki zadatak,
> a ako mu se prikažu samo rješenja i krivi odgovori nema potpunu sliku. Slike + matematika
> renderirana s punim tekstom i ponuđenim odgovorima. I s ispravkom.”

---

## 1. Pregled riješenog testa — što je nedostajalo

Pregled **je postojao** (`ekran_ucenika.prikazi_pregled_rjesenja`, `rjesavanje.pregled_zadatka`),
ali je pokazivao samo tekst zadatka, `Tvoj odgovor: B` i `Točno: C`. Kod višestrukog izbora
sprema se **slovo**, pa je to učeniku značilo točno ništa — nije vidio što je B bio, ni što C.
Slika uz zadatak nije se prikazivala uopće, iako se za vrijeme rješavanja crta.

Dodano:

* **Ponuđeni odgovori** — svi, s tekstom, u istim slovima kao pri pisanju. Tvoj odabir je
  označen ❌ (ili ✅ ako je pogodio), točan ✅. Matematika u opcijama ide kroz isti
  `rjesavanje.pripremi_latex()` kao pri rješavanju, pa se renderira.
* **Slika zadatka** — `slike_zadataka.prikazi_sliku_html()`, isto kao na ekranu rješavanja.
  Ako slika nije dostupna, ispiše se napomena; pregled se ne ruši.
* **`Točno: C) D < 0 i a > 0`** — uz slovo ide i tekst te opcije (`tocan_tekst`).
* **Filtar** Svi / Netočni / Bez odgovora i prekidač **Otvori sve zadatke** (uključen). Prije je
  svaki zadatak trebalo kliknuti posebno — kod 24 zadatka to je 24 klika da se vidi vlastiti test.

**Što se NE odaje prerano:** ponuđeni odgovori vide se uvijek (to je dio zadatka), ali oznaka
točnog odgovora pojavi se tek kad Student View dopusti rješenja. Dotad su svi `tocna=False`.
To čuva test `test_bez_rjesenja_se_tocan_odgovor_ne_odaje`.

Nova čista funkcija `rjesavanje.opcije_pregleda(zadatak, odgovor, pokazi_rjesenje)` — bez
Streamlita, pa je testirana izravno. `pregled_zadatka()` je zadržao sva stara polja, da se
postojeći pozivatelji (`app.py`, stranica učenika) ne slome.

## 2. Uređivanje Student Viewa po testu

Dosad se Student View samo **prikazivao**; postavljao se pri objavi. Sada se mijenja u kartici
🧪 Testovi: šest resursa × tri razine, segmentirano, uz pregled spremljenog stanja.

Nova funkcija **`definicije.postavi_student_view(sheet, definicija, izbor, korisnik="")`**.

Zašto zasebna funkcija, a ne `izmijeni()`: `student_view_json` namjerno nije u `META_POLJA`.
`izmijeni()` upisuje što dobije, a ovdje to ne valja — nepoznat resurs ili razina ne smiju doći
do baze, jer bi ih `_view_iz_jsona()` **tiho preskočio** i učeniku bi se, bez ijedne greške,
prikazalo nešto drugo nego što je profesor postavio. Zato se svaki ključ i svaka razina prvo
provjere protiv `RESURSI` i `STUPNJEVI`.

Pravila:

* **Pokušaji ne blokiraju.** Otvoriti rješenja nakon isteka roka normalan je posao i ne dira
  nijedan predani odgovor.
* **Arhiviran test se ne mijenja** — ista provjera kao za okvirne podatke.
* **Djelomična izmjena** ne briše ostale resurse: krene se od zapisanog stanja.
* Svaka izmjena ide u `Dnevnik_radnji` kao `student_view`, s popisom razina.

U sučelju: ako rješenja ili video stoje na **Uvijek**, pojavi se upozorenje da ih učenik vidi i
prije nego počne pisati, pa odgovori kruže prije roka.

## 3. Testovi

Novo: `testovi/test_pregled_i_student_view.py` — **26 testova**.

| Datoteka | Testova |
|---|---|
| `test_definicije_uredivanje.py` | 24 |
| `test_brisanje_i_arhiva.py` | 30 |
| `test_tema_testovi.py` | 28 |
| `test_zdravlje_koda.py` | 3 |
| `test_pregled_i_student_view.py` | **26** |

**Ukupno 111 testova, svi prolaze:**

```
cd caki-testovi
python -m pytest testovi/ -q        → 111 passed
```

## 4. Otvoreno pitanje — ime stranice učenika

`ARHITEKTURA.md` je do danas navodila **`pages/1_Ucenik.py`**. Takva datoteka ne postoji;
stranica učenika je **`pages/1_Interni_pregled.py`**. Ispravio sam tablicu modula da odgovara
disku, ali ostaje odluka: Streamlit u izborniku stranica ispisuje ime datoteke, pa učenik u
izborniku vidi **„Interni pregled”**. Je li to namjerno (da ne zove na klik) ili zaostatak?
Ako treba, preimenujem u `1_Ucenik.py` — to mijenja i poveznicu koju šalješ učenicima, pa ne
diram bez tvoje riječi.

## 5. Što provjeriti kad digne (poslije Push + Reboot)

1. 🧪 Testovi → odaberi test → **Što učenik vidi**: promijeni razinu, Spremi, osvježi stranicu —
   vrijednost je ostala.
2. Stavi rješenja na **Uvijek** → pojavi se narančasto upozorenje.
3. Odaberi **arhivirani** test → obrazac se ne nudi, samo prikaz.
4. ⚙️ Postavke → `Dnevnik_radnji` → redak `student_view` s popisom razina.
5. 📝 stranica učenika → otvori predani test → **vidiš sve ponuđene odgovore** s tekstom, svoj
   označen, točan označen, i sliku uz zadatak.
6. Isti test prije isteka roka (ako su rješenja na „Poslije”) → opcije se vide, ali **nijedna
   nije označena kao točna**.
7. Filtar **Netočni** → ostaju samo pogrešni; **Otvori sve zadatke** isključi i provjeri da se
   zadaci skupe.

## 6. Ostaje

* `tex_test.py` — napisati `sve_stavke_dolari_neuparene()` (iz prošle isporuke).
* Uređivanje teksta pojedinog zadatka unutar slagalice.
* Biblioteka izvora — nacrt je na platnu, zahvat je u `caki-baza-zadataka`.
* `STATUS.md` još piše „Testovi: 143 prolazi".

---

📌 **COMMIT:** mapa `caki-testovi` → repo `caki-testovi` → grana **main** → ✅ ide uživo nakon Push + Reboot
  · izmijenjeno: `rjesavanje.py`, `ekran_ucenika.py`, `definicije.py`, `app.py`, `upute/ARHITEKTURA.md`
  · novo: `testovi/test_pregled_i_student_view.py`, `upute/UPDATE_20-11_pregled_i_student_view.md`
