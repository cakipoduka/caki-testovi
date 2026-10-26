# 📘 UPDATE 26.10.2026. — 🎓 Zaključne ocjene (šifrarnik)

**Status:** kod radi, **125 testova prolazi** · čeka commit + push + Reboot

---

## 1. Zašto

Na kraju razdoblja profesor ne gleda jedan test, nego **prosjek kroz testove**. Do sada je to morao
računati ručno. Sada kartica **🎓 Ocjene** pokaže sve na jednom mjestu.

## 2. Kako se računa

1. Uzmu se **svi predani** testovi učenika.
2. Prosjek postotaka → predlog ocjene:

| Prosjek | Ocjena |
|---|---|
| 90 %+ | **5 — odličan** |
| 80–89 % | **4 — vrlo dobar** |
| 65–79 % | **3 — dobar** |
| 50–64 % | **2 — dovoljan** |
| < 50 % | **1 — nedovoljan** |

3. Test koji učenik **nije pisao** NE ulazi u prosjek kao nula (izostanak nije znanje). Bilježi se
   odvojeno: *„Testova 1/2 · nije pisao: Test 2 — funkcije"*. Profesor odlučuje što s tim.
4. Učenici **na granici** (49/50, 64/65, 79/80, 89/90) izdvajaju se u upozorenju — tu odluka
   obično nije samo aritmetička.

## 3. Što kartica pokazuje

- **3 brojke gore:** učenika · prosjek razreda · koliko odličnih
- **upozorenja:** tko nema ni jedan test, tko nije pisao sve, tko je na granici
- **tablica:** učenik · šifra · grupa · testova (1/2) · prosjek % · predlog · što nije pisao
- **⬇️ CSV izvoz** za šifrarnik ili e-dnevnik

## 4. Što je namjerno zaštićeno

| Zaštita | Zašto |
|---|---|
| **„predlog je izračun, ne odluka"** — piše u kartici | ocjena je pedagoška odluka, ne formula |
| **izostanak ≠ nula** | jedan izostanak ne smije srušiti ocjenu |
| **učenik bez ijednog testa** ide u skupinu „0" i javlja se | ne dobiva lažnu ocjenu 1 |
| **granični slučajevi se izdvajaju** | 49 % i 50 % nisu isto u odluci |

## 5. Testovi (13 novih, ukupno 125)

`testovi/test_v2_zakljucna.py`:

- pragovi: 49→1, 50→2, 64→2, 65→3, 79→3, 80→4, 89→4, 90→5, 0→1, 100→5
- pragovi se mogu promijeniti bez diranja ostatka
- prosjek i predlog za učenike s 1 i 2 testa
- **nepisani test nije nula** (prosjek 50, ne 25)
- učenik bez ijednog testa → predlog 0 i „—"
- sortiranje po prosjeku, sažetak po ocjenama, prosjek razreda
- upozorenja: bez testova, nije pisao sve, **na granici ocjene**
- tablica za prikaz (ime, 2/2, predlog, što nije pisao)

## 6. Što Caki treba napraviti

1. Commit + push (`zakljucna.py`, `app.py`, `upute.py`, ovaj dokument)
2. Reboot app
3. Kartica **🎓 Ocjene** (puna je kad ima predanih testova)

## 7. Sljedeće

| # | Što |
|---|---|
| 1 | **PDF izvještaj** po učeniku (ocjena + pregled + prilozi) — za roditelje |
| 2 | **više razdoblja** (1. polugodište / 2. polugodište) — filter po datumu |
| 3 | **podsjetnik** učenicima koji nisu otvorili test |
