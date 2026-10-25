# 📘 UPDATE 25.10.2026. — Faza B (1. dio): ekran rješavanja

**Status:** kod radi, **50 testova prolazi** · čeka commit + push + Reboot
**Grana:** `main` (repo `caki-testovi`)

---

## 1. Što je napravljeno

| Modul | Što radi |
|---|---|
| **`ekran_ucenika.py`** *(nov)* | cijeli ekran rješavanja — pitanje po pitanju, navigacija, autosave, predaja; radi i kao **pregled** (`dry=True`) bez ijednog upisa |
| **`rjesavanje.py`** *(nov)* | čista logika: napredak, „što nedostaje", sažetak predaje, povratna informacija po Student View-u, prikaz LaTeX-a |
| **`unos_odgovora.py`** *(nov)* | matematičko polje (MathLive) + automatski fallback na običan tekst |
| **`app.py`** | nova kartica **🧑‍🎓 Kao učenik** (pregled ili stvarni učenik sa šifrom) |
| **`upute.py`** | uputa za novu karticu (unutar aplikacije) |

## 2. Kako radi

1. **Pitanje po pitanju** (ne jedna duga forma): `← Prethodno` / `Sljedeće →`, plus traka
   „Pitanja: 1 ✓ · 2 · · 3 ✓" — učenik odmah vidi gdje je što preskočio.
2. **Napredak i vrijeme** gore: preostalo vrijeme, ukupno bodova, „2/3 odgovoreno" + traka.
3. **Matematički unos** za kratke odgovore; kod višestrukog izbora slova A–E s prikazom LaTeX-a.
4. **Autosave** — odgovor se sprema čim se promijeni (`provedba.spremi`), pa prekid/F5 ne briše rad.
5. **Predaja s upozorenjem** — popis svih pitanja (✅ / ⬜) i rečenica koliko je prazno.
6. **Povratna informacija po Student View-u** — rješenja i 🎬 video **samo** kad smiju
   (`rjesavanje.pregled_zadatka`).

## 3. Što je namjerno zaštićeno

| Zaštita | Zašto |
|---|---|
| **🎬 video se ne prikazuje prije rješenja** | inače bi bio zaobilazni put do odgovora — test to provjerava |
| **„čeka provjeru profesora"** umjesto lažne nule | kad AI/SymPy nisu sigurni, učenik ne smije vidjeti 0 kao konačno |
| **pregled ne piše ništa** | `dry=True` ne dira Sheet — Caki može isprobati sve |
| **autosave ne blokira rješavanje** | ako Google ne odgovori, odgovor ostaje na ekranu i javi se captiсom |
| **stvarni učenik se ne može otvoriti izvan roka** | provjera `dodjele.stanje_roka` prije ulaska |

## 4. Testovi (13 novih, ukupno 50)

`testovi/test_v2_rjesavanje.py`:

- napredak (odgovoreno/prazno/postotak), prazni i `None` odgovori
- oznake pitanja „2 ✓" / „1 ·" i navigacija bez izlaska iz raspona
- „što nedostaje" prije predaje (točan broj praznih + poruka)
- sažetak predaje po pitanju (✅/⬜)
- **video skriven dok rješenja nisu dopuštena**; prikazan kad jesu
- `sto_vidi_ucenik` prati Student View (prije/poslije roka)
- „čeka profesora" i poruka o privremenom rezultatu
- LaTeX pretvorba `\( … \)` → `$ … $`

## 5. Što Caki treba napraviti

1. GitHub Desktop (`caki-testovi`) → **Commit** → **Push**
   (`ekran_ucenika.py`, `rjesavanje.py`, `unos_odgovora.py`, `app.py`, `upute.py`)
2. Streamlit → **Reboot app**
3. Otvori karticu **🧑‍🎓 Kao učenik** → odaberi test → **👁️ Pregled** → probaj riješiti
4. Javi: vidiš li **matematičko polje** (MathLive) ili običan tekst (oba su ispravna, drugi je fallback)

## 6. Sljedeće u Fazi B

| # | Što | Zašto |
|---|---|---|
| 1 | **slike zadataka** iz Drivea (kao portal) | bez toga test s grafom nije upotrebljiv |
| 2 | **💡 AI pomoć** tijekom rješavanja (bez rješenja) | Cakijeva odluka, bot „kao profesor" |
| 3 | **🎬 video** u pregledu rješenja (kartica Rezultati) | već postoji logika, treba prikaz |
| 4 | **prava stranica učenika** (`pages/`) s prijavom po šifri | odvojeno od admina |

> Napomena: baza zadataka je i dalje **po strani** (Caki će javiti kad drugi agent završi). Sustav
> čita kroz `banka.zadatak_iz_retka`; ako se shema promijeni, `⚙️ Postavke → 🩺 Provjera baze` to javi.
