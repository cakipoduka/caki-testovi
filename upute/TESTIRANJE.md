# ✅ TESTIRANJE — cijeli sustav (26.10.2026.)

**Kako koristiti:** idi redom, kvačica kad prođe. Ako nešto ne radi, kopiraj tekst greške i pošalji mi
(ne treba screenshot — tekst je dovoljan).

Trajanje: **~40 minuta** za sve. Ako žuriš, preskoči korake označene ⭐ (napredni).

---

## 0. Priprema (5 min)

| # | Korak | Očekivano |
|---|---|---|
| 0.1 | GitHub Desktop → Commit → Push (`banka.py`, `.gitignore`, i sve ostalo iz popisa) | „No local changes" nakon pusha |
| 0.2 | Streamlit → ⋮ → **Reboot app** | app se podigne bez crvene greške |
| 0.3 | Otvori app → upiši lozinku | ulaziš u „🧪 Testovi — nova generacija" |

**Ako padne:** javi mi tekst greške i u kojoj kartici je.

---

## 1. ⚙️ Postavke — provjera sustava (3 min)

| # | Što gledaš | Očekivano |
|---|---|---|
| 1.1 | **🩺 Provjera sustava** | tri brojke: upis (isključen/uključen) · testova · dodjela |
| 1.2 | otvori **🩺 Provjera baze** | ime Sheeta, broj tabova, **`Zadaci`: N redaka**, zaglavlje |
| 1.3 | ista sekcija | **„Svi stupci koje sustav čita postoje"** ✅ (ne smije više pisati da fale `bodovi` i `bloom`) |
| 1.4 | ako piše da neki neobavezni fali | smije pisati samo `bloom` — to je u redu |
| 1.5 | **🔑 Tajne** | vidiš sve ključeve; `SHEET_ID`, `CRM_SHEET_ID`, `APP_PASSWORD`, `GOOGLE_…` = ✅ |
| 1.6 | **🎬 Video** | ako baza ima `video_url`: zeleno „stupac postoji" |
| 1.7 | **🔧 Pripremi tabove** | kvačica potvrde + gumb → *„Napravljeno: …"* ili *„već postoji"* |

> ⚠️ Prije 1.7 uključi **upis u bočnoj traci** („Uključi upis u živu bazu"), inače je gumb zaključan.

**Prijavi:** ako 1.3 nije zeleno — kopiraj cijeli tekst te poruke.

---

## 2. 🧪 Testovi — sastavi test (5 min)

| # | Korak | Očekivano |
|---|---|---|
| 2.1 | filtriraj po **cjelini** (npr. „Linearne jednadžbe") | broj zadataka se smanji, piše „filtar pronašao N" |
| 2.2 | traži po tekstu (npr. „jednadžb") | pronalazi zadatke |
| 2.3 | označi **3 zadatka** | piše „Odabrano 3 zadatka · X bodova" |
| 2.4 | vidi **bodove** zadatka | moraju biti stvarni (npr. 3), **ne 1** — to je bila greška koju smo popravili |
| 2.5 | upiši naziv `Test probe 1`, trajanje 45, rok (danas–danas+7) | — |
| 2.6 | **💾 Spremi kao nacrt** | *„Spremljeno kao nacrt T26-0001"* |

**Prijavi:** ako je 2.4 uvijek 1 — javi, znači da alias nije uhvatio.

---

## 3. 👥 Objavi — pošalji test (3 min)

| # | Korak | Očekivano |
|---|---|---|
| 3.1 | odaberi `Test probe 1` | gore 4 brojke (zadataka, bodova, rok, dodijeljeno) |
| 3.2 | način **🧑 Šifre učenika** → upiši svoju probnu šifru (npr. `TEST01`) | gumb „📤 Objavi" se uključi |
| 3.3 | **📤 Objavi** | *„Dodano 1 učenika"*; test prelazi u „objavljen" |
| 3.4 | ponovi istu šifru i objavi još jednom | **preskočeno** (ne dopisuje duplikat) |
| 3.5 | tablica „Kome je poslan" | vidiš šifru, status, rok |

---

## 4. 📝 Stranica učenika — rješavanje (10 min) ⭐ NAJVAŽNIJE

**Otvori u bočnoj traci: „Ucenik"** (nova stranica, odvojena od admina).

| # | Korak | Očekivano |
|---|---|---|
| 4.1 | prijava šifrom `TEST01` | popis „Moji testovi" s testom `Test probe 1` |
| 4.2 | klik **▶ Počni** | otvara se rješavanje: gore **preostalo vrijeme**, bodovi, „0/3 odgovoreno" |
| 4.3 | traka pitanja | „1 · · 2 · · 3 ·" |
| 4.4 | **upiši odgovor** u matematičko polje | polje prima unos (MathLive ili običan tekst) |
| 4.5 | **osvježi stranicu (F5)** | odgovor **ostaje** (autosave) — to je ključna provjera |
| 4.6 | klik **Sljedeće →** | ide na pitanje 2, prvo je označeno ✓ |
| 4.7 | ako zadatak ima sliku | slika se prikaže (ili poruka „javi Cakiju") |
| 4.8 | otvori **💡 Trebaš pomoć?** | piše „Još 3 pitanja…" i polje za pitanje |
| 4.9 | pošalji pitanje (npr. „ne znam početi") | odgovor bota **bez konačnog rješenja**; brojač se smanji |
| 4.10 | **✅ Predaj** | popis 1 ✅ / 2 ⬜ …, pa *„Predano: X / Y bodova"* |
| 4.11 | nakon predaje | ako rješenja nisu dopuštena: *„Rješenja će biti dostupna nakon isteka roka"* |

**Prijavi:** 4.5 (autosave) i 4.9 (AI) su najosjetljiviji — ako padnu, kopiraj što piše.

---

## 5. 📷 Prilog rada — učenik sam šalje sken (3 min)

| # | Korak | Očekivano |
|---|---|---|
| 5.1 | u kartici testa otvori **📷 Priloži svoj rad** | polje za datoteku + polje za poveznicu |
| 5.2 | odaberi bilo koju sliku s računala → **📤 Pošalji rad** | *„Rad je poslan profesoru ✅"* |
| 5.3 | ponovno otvori | piše „Već priloženo: 1 rad(a) — 1 čeka potvrdu" |
| 5.4 | pošalji i **poveznicu** (bilo koji URL) | prihvaćeno — fallback radi |

**Ako 5.2 padne:** javi tekst (moguće da `RADOVI_FOLDER_ID` nije podijeljen s testnim računom) — poveznica mora raditi u svakom slučaju.

---

## 6. 📊 Rezultati (7 min)

| # | Korak | Očekivano |
|---|---|---|
| 6.1 | odaberi test | 3 brojke: predalo, prosjek, raspon; tablica s mjestom |
| 6.2 | ispod tablice | „Nije predalo: …" (ako ima) |
| 6.3 | **⬇️ Preuzmi rezultate (CSV)** | datoteka se otvori u Excelu s hrvatskim znakovima |
| 6.4 | otvori učenika (sklopivo) | „📷 Papirnati dio: 1 rad(a) — 1 čeka potvrdu" + link na rad |
| 6.5 | klik **✅ Potvrdi pregled** | piše „Pregled potvrđen", stanje se promijeni |
| 6.6 | **📄 Izvještaj za roditelje (PDF)** | PDF s **nazivom firme, sloganom, webom i e-mailom** u podnožju |
| 6.7 | u PDF-u | piše **„Ostvareni rezultat"** (NE „predlog ocjene"); kvačice č/ć/ž/š rade |
| 6.8 | isto kao HTML | isti sadržaj, isti kontakt |
| 6.9 | **👀 Praćenje pristupa** | tablica: šifra, posjeta, testova, zadnji put |
| 6.10 | **📨 Koga podsjetiti** | 4 brojke + tablica + tekst za kopiranje |
| 6.11 | pregled rješenja po učeniku | po zadatku: tvoj odgovor, točno, 🎬 video (ako postoji) |

**Prijavi:** 6.6/6.7 (PDF izgled) i 6.9 (praćenje) — to su nove stvari.

---

## 7. 📈 Kvaliteta (3 min)

| # | Korak | Očekivano |
|---|---|---|
| 7.1 | odaberi test | 4 brojke: predanih, prosjek, **α**, zadataka |
| 7.2 | s malo učenika | **upozorenje** „Manje od 10 predanih — brojke su orijentacijske" |
| 7.3 | tablica po zadatku | p, r, ocjena težine, razlikuje?, preporuka na hrvatskom |
| 7.4 | tablica po cjelinama | koja cjelina pada |
| 7.5 | distraktori | trake s koliko je koji odgovor biran, „⚫ mrtav" |

> S 1 probnim učenikom brojke su **besmislene po prirodi** — bitno je da se stranica ne ruši i da
> upozorenje radi.

---

## 8. 🎓 Ocjene (2 min)

| # | Korak | Očekivano |
|---|---|---|
| 8.1 | kartica 🎓 Ocjene | učenika · prosjek razreda · koliko odličnih |
| 8.2 | upozorenja | tko nema test, tko nije pisao sve, tko je na granici |
| 8.3 | tablica | učenik, 1/1 testova, prosjek %, predlog ocjene |
| 8.4 | **⬇️ Preuzmi ocjene (CSV)** | otvara se u Excelu |

---

## 9. Regresija — stare aplikacije (2 min)

| # | Provjera |
|---|---|
| 9.1 | otvori `caki-baza-zadataka` → radi kao prije (nema crvene greške) |
| 9.2 | otvori `caki-booking-termina` (portal) → radi |
| 9.3 | `caki-testovi` i dalje radi nakon toga |

---

## Što mi javiti

**Ako sve prođe:** samo „prošlo" + koje korake si preskočio.

**Ako nešto padne**, pošalji:
1. **broj koraka** (npr. 4.5)
2. **točan tekst** poruke (kopiraj iz ekrana)
3. u kojoj je kartici

Ne treba screenshot — tekst je dovoljan.

---

## Poznate stvari (nisu greške)

| Pojava | Zašto |
|---|---|
| ⚠️ „Baza … izgleda kao kopija/backup" | `SHEET_ID` pokazuje na kopiju od 22.10. — čeka se da drugi agent završi |
| PDF: **Đ** možda nije ispravan | dok ne staviš `fontovi/DejaVuSans.ttf` |
| Kvaliteta: „orijentacijske brojke" | manje od 10 predanih radova |
| α = 0 ili prazno | premalo učenika za pouzdanost |
| Ocjene: predlog „—" | učenik nema ni jedan predan test |
