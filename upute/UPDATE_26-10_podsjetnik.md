# 📘 UPDATE 26.10.2026. — 📨 Koga podsjetiti

**Status:** kod radi · čeka commit + push + Reboot

---

## 1. Što je

U 📊 Rezultatima, sklopivo **📨 Koga podsjetiti (i što mu napisati)**:

- **4 brojke:** nije otvorio portal · otvorio a nije počeo · počeo a nije predao · predao
- **tablica** onih koji trebaju podsjetnik (najhitniji prvi)
- **tekst za kopiranje** — poruke prilagođene svakom slučaju, spremne za WhatsApp ili e-mail

## 2. Zašto tri različite poruke

Poruka „nisi ni otvorio test" učeniku koji je test **počeo** izgleda kao da ga sustav ne poznaje i
odmah gubi povjerenje. Zato:

| Stanje | Poruka |
|---|---|
| nije otvorio | „…test te još čeka i nije otvoren. Prijavi se sa svojom šifrom." |
| otvorio, nije počeo | „…otvaranje testa **ne pokreće vrijeme** — počni kad si spreman." |
| počeo, nije predao | „…odgovori su **spremljeni** — otvori portal i predaj kad završiš." |

Treća poruka je najvažnija: smiruje učenika da nije izgubio rad (i to je istina — autosave radi).

## 3. Zašto aplikacija ne šalje poruke

Slanje e-maila/WhatsAppa traži dodatne servise i Cakijeve račune. Zato aplikacija **pripremi tekst**,
a Caki ga pošalje svojim kanalom (grupa, e-mail, roditelj). Kasnije se može dodati automatsko slanje.

## 4. Testovi (10 novih)

`testovi/test_v2_podsjetnik.py`: kategorije po stvarnom stanju · **predali se ne podsjećaju** ·
najhitniji prvi · svi redci kad se traži · brojke po skupinama · prazno ne ruši · **tri različite
poruke** (i njihov sadržaj) · sve poruke u jednom tekstu za kopiranje.

## 5. Što Caki treba napraviti

1. Commit + push (`podsjetnik.py`, `app.py`, ovaj dokument)
2. Reboot app
3. 📊 Rezultati → odaberi test → **📨 Koga podsjetiti** → kopiraj tekst

## 6. Sljedeće

| # | Što |
|---|---|
| 1 | **PDF s fontom** (izravni PDF izvještaj) |
| 2 | **razdoblja** (1./2. polugodište) |
| 3 | **automatsko slanje** podsjetnika (e-mail) ako Caki želi |
