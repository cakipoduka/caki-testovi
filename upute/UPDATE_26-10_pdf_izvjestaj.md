# 📘 UPDATE 26.10.2026. — 📄 Pravi PDF izvještaj (bez ispisa)

**Status:** kod radi, **151 test prolazi** · čeka commit + push + Reboot

---

## 1. Rješenje problema s fontom

Prije: reportlab dolazi bez fontova za **č, ć, ž, š, đ** — PDF bi imao kvadratiće ili „Curic”.

**Nađeno rješenje:** `Vera.ttf` **već dolazi uz reportlab** (66 KB, slobodna licenca) i pokriva
**sva hrvatska slova**. Provjereno programski:

| Znak | U+ | Ima? |
|---|---|---|
| č | 010D | ✅ |
| ć | 0107 | ✅ |
| ž | 017E | ✅ |
| š | 0161 | ✅ |
| đ | 0111 | ✅ |
| Č Ć Ž Š Đ | 010C 0106 017D 0160 0110 | ✅ |

Zato **nema preuzimanja ni dodavanja fonta u repo** — PDF odmah ima ispravne kvačice.

## 2. Što PDF sadrži

- naslov **„Izvještaj — Ana Čurić”**
- šifra · grupa · datum
- **ukupno**: postotak + predlog ocjene (npr. „85 % — predlog ocjene 4 (vrlo dobar)")
- **tablica testova**: naziv · datum · bodovi · postotak
- **priloženi radovi** (pregledano / čeka pregled)
- napomena (ako je upišeš)
- podnožje: odakle je izvještaj i što prazan zadatak znači

## 3. Gumbi u 📊 Rezultatima

| Gumb | Kada koristiti |
|---|---|
| **📄 Izvještaj za roditelje (PDF)** | kad treba datoteka za e-mail ili ispis |
| 📄 Izvještaj za roditelje (HTML → ispiši kao PDF) | ako PDF ne radi (fallback) |

**Ako PDF ne uspije, stranica se ne ruši** — piše zašto i nudi HTML.

## 4. Testovi (8 novih, ukupno 151)

`testovi/test_v2_pdf.py`:

- **font pokriva sva hrvatska slova** (najvažniji test — bez toga PDF je bezvrijedan)
- registracija fonta prolazi
- generirani dokument je **pravi PDF** (`%PDF` … `%%EOF`), veći od 1,5 KB
- dokument je valjan i **raste s podacima** (više testova → veći PDF)
- bez testova ne ruši
- radovi i napomena ulaze u dokument
- sigurno ime datoteke (`Ana_Curic_izvjestaj.pdf`)
- prazan učenik ne ruši

> Napomena: PDF je komprimiran, pa se tekst **ne može** tražiti u sirovim bajtovima — zato se kvačice
> jamče provjerom pokrivenosti fonta, a ne pretragom stringa.

## 5. Što Caki treba napraviti

1. Commit + push (`pdf_izvjestaj.py`, `app.py`, ovaj dokument)
2. Reboot app
3. 📊 Rezultati → uz učenika → **📄 Izvještaj za roditelje (PDF)** → otvori datoteku

## 6. Sljedeće

| # | Što |
|---|---|
| 1 | **razdoblja** (1./2. polugodište) — filter po datumu |
| 2 | **PDF za cijeli razred** (jedan dokument, svi učenici) |
| 3 | **logotip i potpis** u PDF-u |
