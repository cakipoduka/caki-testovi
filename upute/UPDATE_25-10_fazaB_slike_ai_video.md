# 📘 UPDATE 25.10.2026. — Faza B (2. dio): slike, 💡 pomoć, video u rezultatima

**Status:** kod radi, **67 testova prolazi** · čeka commit + push + Reboot

---

## 1. Što je dodano

| Modul | Što radi |
|---|---|
| **`slike_zadataka.py`** *(nov)* | prikaz **slike uz zadatak** iz Drivea (isti sustav kao portal). Traži `SLIKE_FOLDER_ID`, `..._MATEMATIKA_OS`, `..._FIZIKA` — sve ključeve koje Caki već ima |
| **`ai_pomoc.py`** *(nov)* | **💡 pomoć tijekom rješavanja** — bot pomaže razumjeti, **nikad ne daje rješenje**; max 3 pitanja po zadatku |
| `ekran_ucenika.py` | slika umjesto napomene + 💡 blok uz svako pitanje |
| `app.py` | 📊 Rezultati: **pregled rješenja po učeniku** s 🎬 videom |

## 2. Slike — kako radi

- U bazi je zapisano samo **ime datoteke** (`slika` u zadatku).
- Modul ime pretvori u Drive ID i dohvati bajtove (bez novog paketa — `google-auth` + `requests`).
- **Keš u memoriji** (do 300 slika) — isti zadatak se ne skida pri svakom rerunu.
- Ako foldera nema u Secrets → **ne ruši ekran**, samo kratka napomena.
- Prenesena je i **tolerantna obrada JSON-a** servisnog računa (isti bug s pametnim navodnicima).

## 3. 💡 AI pomoć — pravila ugrađena u kod

Sistemski prompt (u kodu, `ai_pomoc.PRAVILA`):

> 1. **NIKAD** ne reci konačan odgovor ni broj koji je rješenje.
> 2. Ne rješavaj zadatak do kraja — daj putokaz, pitanje ili podsjetnik na formulu.
> 3. Najviše 3 rečenice. Bez predgovora.
> 4. Piši hrvatski, jednostavno.
> 5. Ako učenik traži rješenje, odbij i ponudi prvi korak.

**Ključna zaštita (testirana):** u upit **ne ulazi** polje `odgovor` iz baze. Test to dokazuje tako
što stavi oznaku `TAJNA123` u `odgovor` i provjeri da se ne pojavljuje u porukama.

Ostalo: max **3 pitanja po zadatku** (broji se u sesiji), odgovor se pamti u razgovoru, a pad API-ja
ili nedostatak ključa **ne blokira rješavanje** (samo kratka napomena).

Tajna: `DEEPSEEK_API_KEY` (primarno) ili `ANTHROPIC_API_KEY`.

## 4. 🎬 Video u rezultatima

- Učenik ga vidi **samo** kad Student View dopušta **rješenja** (inače bi bio zaobilazni put do odgovora).
- **Profesor** u 📊 Rezultatima vidi video uvijek, uz svakog učenika (sklopivi pregled po zadatku).

## 5. Testovi (17 novih, ukupno 67)

| Datoteka | Broj | Što pokriva |
|---|---|---|
| `test_v2_slike.py` | 5 | tolerantno čitanje ključa (pametni navodnici, prijelomi, smeće), prikaz bez foldera ne ruši |
| `test_v2_ai_pomoc.py` | 12 | pravila zabranjuju rješenje, **odgovor ne ulazi u upit**, ograničenje pitanja, HTTP greška, iznimka, oba formata odgovora |
| *(prije)* | 50 | temelj, veza, rješavanje, aplikacija |

## 6. Što Caki treba napraviti

1. GitHub Desktop (`caki-testovi`) → **Commit** → **Push**
   (`slike_zadataka.py`, `ai_pomoc.py`, `ekran_ucenika.py`, `app.py`)
2. **Secrets** → dodaj `DEEPSEEK_API_KEY` (bez toga 💡 pomoć samo piše „nije uključena")
3. **Reboot app**
4. Probaj: **🧑‍🎓 Kao učenik → 👁️ Pregled** → vidiš li sliku (ako zadatak ima `slika`) i 💡 blok

## 7. Sljedeće

| # | Što |
|---|---|
| 1 | **prava stranica učenika** (`pages/`) — prijava šifrom, bez admin kartica |
| 2 | **unos slika/radova** (📷 skenovi) — papir + ekran |
| 3 | **mjerenje kvalitete zadatka** (p, diskriminativnost, distraktori) — Faza C |
