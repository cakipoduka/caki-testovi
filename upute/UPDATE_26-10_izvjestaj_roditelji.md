# 📘 UPDATE 26.10.2026. — 📄 Izvještaj za roditelje

**Status:** kod radi · čeka commit + push + Reboot

---

## 1. Što je

U 📊 Rezultatima, uz svakog učenika, gumb **📄 Izvještaj za roditelje** — jedan dokument s:

- imenom, šifrom i grupom učenika
- **ukupnim postotkom i predlogom ocjene**
- tablicom svih testova (datum, bodovi, postotak)
- **priloženim radovima** (pregledano ✅ / čeka ⏳)
- napomenom (ako je upišeš)

## 2. Zašto HTML, a ne PDF

PDF knjižnica (reportlab) dolazi **bez fontova za č, ć, ž, š, đ** — slova bi ispala kao kvadratići ili
bi ih trebalo pisati bez kvačica („Curic” umjesto „Čurić”). Za izvještaj koji ide roditelju to nije
prihvatljivo.

HTML nema taj problem: otvori se u browseru i ispiše kao PDF — **Ctrl+P → Save as PDF**. Hrvatski
znakovi rade, nema dodatnih paketa, dokument se otvara na svakom mobitelu i računalu.

> Ako Caki želi izravni PDF bez ispisa, treba **jedan font s hrvatskim znakovima** u repo (npr.
> DejaVuSans.ttf, ~700 KB, slobodna licenca). Tada dodajem PDF u pola sata. HTML je privremeno rješenje
> koje **radi odmah**.

## 3. Sigurnost

Tekst zadatka dolazi iz baze i može sadržavati `<`, `&`, navodnike. Sve se **escapira**
(`html.escape`), pa naslov poput `<script>alert(1)</script>` završi kao običan tekst. Test to provjerava.

## 4. Testovi (8 novih)

`testovi/test_v2_izvjestaj.py`: dokument nastaje i ima ispravan početak/kraj · č i ć **ostaju** ·
prosjek 85 % i predlog „vrlo dobar (4)" · **escapiranje** `<script>` · bez testova ne ruši ·
radovi i napomena u dokumentu · sigurno ime datoteke (`Ana_Curic_izvjestaj.html`) · prazan učenik.

## 5. Što Caki treba napraviti

1. Commit + push (`izvjestaj.py`, `app.py`, ovaj dokument)
2. Reboot app
3. 📊 Rezultati → uz učenika → **📄 Izvještaj za roditelje** → otvori → Ctrl+P

## 6. Sljedeće

| # | Što |
|---|---|
| 1 | **PDF s fontom** (ako Caki želi izravni PDF) |
| 2 | **razdoblja** (1./2. polugodište) — filter po datumu |
| 3 | **podsjetnik** učenicima koji nisu otvorili test |
