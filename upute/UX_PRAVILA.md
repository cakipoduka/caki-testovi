# 🎨 UX/UI pravila — CAKI sustav testiranja

**Cakijeva uputa 26.10.2026.:** *„UX i UI uvijek imati na umu — preglednost, jednostavnost korištenja."*

Vrijedi za **svaku** karticu i svaku novu funkciju. Ako funkcija radi, a korisnik ne zna gdje je —
**nije gotova**.

---

## 1. Jedan posao = jedno mjesto

| Pravilo | Primjer iz prakse |
|---|---|
| Ne dijeliti isti tok na dva ekrana | slaganje testa je prvo bilo u dva taba (PDF / online) → **spojeno u 🧱 Složi test** |
| Ako se isti odabir koristi dvaput, dijeli se | odabrani zadaci vrijede i za PDF i za online |
| Kartica = jedna faza posla | 🧪 Testovi (molim) · 🧱 Složi test · 👥 Objavi · 📊 Rezultati · 📈 Kvaliteta · 🎓 Ocjene |

## 2. Gumb, ne kvadratić

| Loše | Dobro |
|---|---|
| mali `checkbox` uz svaki zadatak | **➕ Dodaj** gumb + **✓ već dodano** umjesto gumba |
| „označi pa negdje dalje primijeni" | radnja se vidi odmah, uz zadatak |

**Zašto:** kvadratić se na mobitelu i u žurbi promaši; gumb je velika meta i ima jasan ishod.

## 3. Odabir mora biti vidljiv cijelo vrijeme

- **desni stupac „📋 Odabrano (N)"**: naslovi, bodovi, ✕ za uklanjanje, ukupno bodova
- korisnik nikad ne mora pamtiti što je odabrao
- **nikad dupli unos** — ako je već unutra, piše **„✓ već dodano"**

## 4. Reci što slijedi

- ako je gumb zaključan — **napiši zašto** („Napiši naslov", „Zbroj po kategorijama 1 ≠ 2")
- ako nešto traje — reci koliko („stranica 2/5, zadaci 21–40 od 173")
- nakon radnje — potvrda s konkretnim podatkom („Spremljeno kao nacrt **T26-0007**")

## 5. Nikad sirovi podaci korisniku

| Loše | Dobro |
|---|---|
| `\(2x+1=5\)` u popisu | prikaz kao formula |
| `predano` / `u_tijeku` | ✅ Predano · ⏳ U tijeku |
| `{'UZV': '1'}` | „UZV: 1 bod." |
| `T26-0007` bez imena | „**Kvadratna jednadžba** (T26-0007)" |

## 6. Postupno otkrivanje

- osnovno vidljivo, napredno u **sklopivi blok** (`Pripremi tabove`, `Zašto se slike ne vide`)
- upute **unutar** ekrana, sklopljene — nikad zasebna stranica
- prazno stanje mora **reći što napraviti** („Još nema testa → napravi ga u 🧪 Testovi")

## 7. Sigurnost bez straha

- opasne radnje (upis u živu bazu) traže **potvrdu i objašnjenje posljedice**
- ako funkcija padne, **ostatak ekrana radi** (svaka kartica u `try/except`)
- nikad `st.stop()` unutar kartice — gasi cijelu stranicu

## 8. Provjera prije isporuke (5 pitanja)

1. Može li se posao završiti **bez vraćanja** na prethodni ekran?
2. Vidi li se **uvijek** što je odabrano?
3. Je li svaki zaključan gumb **objasnio zašto** je zaključan?
4. Ima li ekran **prazno stanje** s uputom?
5. Bi li to razumjelo dijete od 15 godina bez objašnjenja?

> Ako je odgovor na ijedno „ne" — funkcija nije gotova, bez obzira na to što radi.
