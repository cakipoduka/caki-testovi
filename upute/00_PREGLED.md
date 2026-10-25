# 📚 Arhiva razvoja — `caki-testovi`

Ovdje stoji **povijest razvoja** nove aplikacije za testiranje: izvještaji po isporuci, kratke upute i
arhitektura. Ista praksa kao za razvoj CRM-a (`CAKI_razvoj/upute/`), samo što ova mapa živi **uz kod**
(pa se arhivira zajedno s njim).

---

## Što je ovdje

| Datoteka | Što je |
|---|---|
| **`KAKO_POKRENUTI.md`** | kratka uputa: tajne, prvi ulazak, sigurnosne kočnice, rješavanje problema |
| **`ARHITEKTURA.md`** | moduli, model podataka, pravila koja se ne krše |
| **`DNEVNIK.md`** | jedna linija po isporuci — brzi pregled povijesti |
| **`UPDATE_DD-MM_tema.md`** | izvještaj po isporuci (što je napravljeno, odluke, bugovi, testovi, sljedeće) |

## Kako se piše izvještaj (pravilo)

1. **Naziv:** `UPDATE_DD-MM_kratka_tema.md` (npr. `UPDATE_25-10_fazaA_temelj.md`).
2. **Obavezni dijelovi:** status · što je napravljeno · odluke ugrađene · bugovi nađeni i popravljeni ·
   testovi (broj) · **što Caki treba napraviti** · što je sljedeće.
3. **Ne prepisuje se povijest.** Ako se nešto promijeni, dodaje se nova datoteka i unos u `DNEVNIK.md`.
4. **Ne pišu se tajne.** Nikad lozinke, ključevi ni ID-evi koji nisu javni.
5. **Svaka tvrdnja o radu mora imati dokaz** (test, broj, ili „nije provjereno").

## Što je *izvan* ove mape (globalna arhiva)

| Mapa | Što drži |
|---|---|
| `CAKI_razvoj/upute/` | globalni dokumenti: `MASTER_SUSTAV_TESTIRANJA.md`, `ANALIZA_24-10_*`, svi UPDATE-i za sve aplikacije |
| `CAKI_razvoj/TRACKER.md` | koordinacija: otvorene odluke (§2), dnevnik svih agenata (§5), što nije riješeno (§7) |
| `CAKI_razvoj/DeepSeek_updates.md` | kronologija po ciklusima |

> Pravilo: **ovdje** ide ono što treba onome koji radi na ovom kodu. **Globalno** ide sve što dira više
> aplikacija ili treba Cakiju za odluke.

## Dosadašnje isporuke

| Datum | Faza | Izvještaj |
|---|---|---|
| 25.10.2026. | **Faza A** — temelj (test kao zapis, dodjele, ocjenjivanje, autosave, aplikacija s 4 kartice) | `UPDATE_25-10_fazaA_temelj.md` |
