# UPDATE 20.11.2026. — uredivanje testa odblokirano + arhiva kao biblioteka predlozaka

Prioriteti za nocas (Cakijev popis): **1. odblokirati uredivanje** i **3. biblioteka predlozaka**.
Tocka 2 (uredivanje sadrzaja) rijesena je onako kako je Caki rekao: **kopija predloska -> uredi kao novi test**.

## 1. Sto je bilo pokvareno

| Simptom | Pravi uzrok |
|---|---|
| „Urediivanje nije moguce: Rok je poceo 29.10.2026." iako test nitko nije otvorio | `definicije.smije_urediti()`, pravilo 4: cisto provjeravanje datuma, bez gledanja ima li ijedan pokusaj |
| Test s predanim pokusajima nije se mogao ni preimenovati ni dobiti novi rok | `izmijeni()` je trazila `smije_urediti()`, a ta funkcija cuva ZADATKE — iako `izmijeni()` zadatke nikad ne dira |
| Uvezeni v1 testovi nisu se mogli ni otvoriti ni vratiti | `uvoz_v1` svaki stari test upisuje sa statusom `arhiviran`, a iz arhive nije postojao izlaz — rijec „arhiviran" u `app.py` nije se pojavljivala ni jednom |
| Popis testova zagusen starim testovima | `_testovi()` namjerno vraca i arhivirane, bez filtra u sucelju |
| Gumb Deaktiviraj/Aktiviraj bi pao | `_status_l` je u `app.py` bio koristen, a nigdje postavljen (NameError; nije se vidio jer je uredivanje bilo zakljucano prije njega) |

## 2. Dvije razine zastite (nova logika)

* `smije_urediti()` — cuva **ZADATKE**. Blokira: arhiviran test, i test koji ima **ijedan pokusaj**.
  Rok koji je poceo **vise ne blokira** ako nitko nije otvorio test: dokaz cuva `Pokusaji.zadaci_json`
  (snimka pitanja koja je ucenik stvarno vidio), pa bez pokusaja nema sto pokvariti. Vraca upozorenje (⚠️).
* `smije_urediti_metapodatke()` — **NOVO**, cuva samo arhivu. Naziv, trajanje, rok i AI pomoc
  (`META_POLJA`) smiju se mijenjati i kad test ima predane pokusaje. Produljiti rok je normalan posao.
* `izmijeni()` od sada trazi drugu provjeru. `zadaci_json` i dalje nije na popisu dopustenih polja.

## 3. Arhiva = biblioteka predlozaka

* `arhiviraj()` — status `arhiviran`. **Nije brisanje**: dodjele, pokusaji i ocjene ostaju.
* `vrati_iz_arhive()` — natrag u `zatvoren` (Caki vidi i smije mijenjati, ucenik ne).
  Namjerno NE u `objavljen`, jer objava znaci dodjele i ide kroz 👥 Objavi.
* **Odluka koju sam donio bez tvoje potvrde** (pitanje je ostalo bez odgovora, a trebalo je za nocas):
  arhiviranje je **povratno**. Arhiva iz koje se ne moze natrag zakljucala bi ti sve uvezene v1 testove
  zauvijek — tocno ono na sto si se zalio. Ako zelis da bude konacno, javi i vadim `vrati_iz_arhive` iz sucelja.

## 4. Sto se mijenja u sucelju (🧪 Testovi)

* **🗄️ Prikaži i arhivirane (N)** — prekidac nad popisom; arhivirani su skriveni dok ih ne ukljucis.
* **✏️ Uredi sadržaj (kao novi test)** — ucita zadatke tog testa u 🧱 Složi test (zajedno s naslovom
  „… (kopija)"), prebaci te na tu karticu i tamo slobodno dodajes, izbacujes, mijenjas redoslijed i bodove.
  Spremanje pravi **novi** test; izvorni ostaje nedirnut. To je tocka 2 s tvog popisa.
* **🗄️ Arhiviraj** — pored Kloniraj.
* **↩️ Vrati iz arhive** — vidi se kad je odabrani test arhiviran.
* Kad su zadaci zakljucani (test ima pokusaje), obrazac se **vise ne gasi**: dobijes plavu poruku da su
  zadaci zakljucani, a naziv/rok/trajanje/AI mijenjas normalno.

## 5. Testovi

Novo: `testovi/test_definicije_uredivanje.py` — **24 testa, svi prolaze** (`python -m pytest testovi/test_definicije_uredivanje.py -q`).
Pokrivaju: rok poceo bez pokusaja, pokusaj zakljucava zadatke, arhiviran se ne mijenja, meta uz pokusaje,
`izmijeni()` odbacuje `zadaci_json`, cijeli put arhiva -> iz arhive -> uredivanje otvoreno, i staticku provjeru
`app.py` (`_status_l` postavljen prije upotrebe, gumbi povezani, slagalica se puni pravim ključem).

Postojeci testovi u `testovi/` (`test_admin_app.py`, `test_portal.py`, `test_matura_dolasci.py`) su CRM testovi
i ne diraju `caki-testovi` — **pokreni `python -m pytest -q` u `testovi/` kod sebe** da potvrdis da su i dalje zeleni.

## 6. Sto provjeriti kad digne (poslije Push + Reboot)

1. 🧪 Testovi -> odaberi test kojem je rok poceo, a nitko ga nije otvorio -> obrazac je otvoren, pise ⚠️.
2. Odaberi test s predanim pokusajima -> plava poruka „Zadaci su zakljucani", ali rok se mijenja.
3. 🗄️ Prikaži i arhivirane -> vidis uvezene v1 testove -> ↩️ Vrati iz arhive -> status `zatvoren`.
4. ✏️ Uredi sadržaj (kao novi test) -> baca te u 🧱 Složi test s ucitanim zadacima i naslovom „… (kopija)".
5. 🗄️ Arhiviraj neki stari test -> nestaje s popisa dok ne ukljucis prekidac.

## 7. Ostaje (nije u nocasnjem opsegu)

* Tvoja skica sucelja — raspored kartica cekam pa da ga slozim po njoj.
* Uredivanje teksta pojedinog zadatka unutar slagalice (sad se zadatak izbaci i doda ispravljeni iz baze).
* `UVOZ_FOLDER_ID` u Secrets (iz prosle isporuke).
* Hardkodirana putanja `C:\Users\Caki\Desktop\...` u `test_skupine_ui.py` (baza zadataka, nije ovdje).

---

📌 **COMMIT:** mapa `caki-testovi` -> repo `caki-testovi` -> grana **main** -> ✅ ide uzivo nakon Push + Reboot
📌 **COMMIT:** mapa `CAKI_razvoj/testovi` -> nije u gitu (testovi i dokumentacija) -> nema commita
