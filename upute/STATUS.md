# 📊 STATUS — gdje je sustav danas (26.10.2026.)

**Jedna stranica za brzi pregled.** Detalji su u `UPDATE_*.md`, arhitektura u `ARHITEKTURA.md`.

---

## Radi od početka do kraja

| Korak | Gdje | Stanje |
|---|---|---|
| 1. Sastavi test iz baze (filtri, odabir zadataka) | 🧪 Testovi | ✅ |
| 2. Objavi grupi/kanti/pojedincu, dopuni nakon objave | 👥 Objavi | ✅ |
| 3. Učenik se prijavi šifrom i rješava (pitanje po pitanju, autosave) | 📝 stranica Ucenik | ✅ |
| 4. Matematički unos, slike zadataka, 💡 pomoć (bez rješenja) | u rješavanju | ✅ |
| 5. Predaja s upozorenjem (koliko je prazno) | u rješavanju | ✅ |
| 6. Učenik fotografira papir i pošalje ga | 📷 u stranici učenika | ✅ |
| 7. Profesor vidi rang, prosjek, ko nije predao | 📊 Rezultati | ✅ |
| 8. Pregled rješenja s 🎬 videom (po Student View-u) | 📊 Rezultati | ✅ |
| 9. Kvaliteta zadataka (p, r, distraktori, α) po cjelinama | 📈 Kvaliteta | ✅ |
| 10. Predlog zaključne ocjene + CSV | 🎓 Ocjene | ✅ |
| 11. Izvještaj za roditelje (**PDF** i HTML) | 📊 Rezultati | ✅ |
| 12. Koga podsjetiti + tekst poruke | 📊 Rezultati | ✅ |
| 13. Praćenje pristupa (koliko puta je učenik bio) | 📊 Rezultati | ✅ |

**Testovi: 143 prolazi.** Nijedan stari repo nije diran. Živa baza se samo čita.

## Što još nije napravljeno

| # | Što | Zašto čeka |
|---|---|---|
| 1 | **razdoblja** (1./2. polugodište) | filter po datumu u Ocjenama i Rezultatima |
| 3 | **automatsko slanje** podsjetnika | treba e-mail servis |
| 4 | **live kviz** (Kahoot stil) | Cakijeva odluka: kasnije faze |
| 5 | **prijevod i više škola** | arhitektura pripremljena (`ustanova_id`, `jezik`) |

## Prije nego pusti učenike

1. `SHEET_ID` mora pokazivati na **živu bazu** (trenutno kopija od 22.10. — aplikacija to javi crvenim).
2. ⚙️ Postavke → **Pripremi tabove** (6 tabova + `Radovi`, `Posjete`).
3. Uključi upis u bočnoj traci (ili `V2_UPIS = "da"`).
4. Pošalji učenicima link na **stranicu Ucenik** — ne na admin.
5. Provjeri Student View po testu (rješenja i video tek nakon roka).

## Pravila koja se ne krše

- Baza zadataka (`Zadaci`) se **nikad ne mijenja** iz ove aplikacije.
- Upis u CRM je **isključen** dok ga ne uključiš.
- Predani rad se **ne prepisuje**; ručna ocjena ostavlja trag tko je i kada.
- **AI samo predlaže** — konačnu ocjenu daje profesor.
