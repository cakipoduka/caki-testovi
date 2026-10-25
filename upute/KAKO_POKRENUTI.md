# 🧪 CAKI testovi v2 — kako se pokreće

**Kratka uputa.** Detalji su u `UPDATE_*.md`, arhitektura u `ARHITEKTURA.md`.

---

## 1. Što ova aplikacija jest

Nova generacija sustava testiranja. **Paralelni razvoj** — stara tri repoa (`caki-baza-zadataka`,
`caki-booking-termina`, `caki-upisi-crm-main`) rade dalje i ne diraju se.

Gradi se po `CAKI_razvoj/upute/MASTER_SUSTAV_TESTIRANJA.md`.

## 2. Pokretanje lokalno (nije obavezno)

```powershell
cd C:\Users\Caki\Desktop\CAKI_razvoj\caki-testovi
pip install -r requirements.txt
mkdir .streamlit
notepad .streamlit\secrets.toml     # zalijepi tajne (v. dolje)
streamlit run app.py
```

`.streamlit/secrets.toml` je u `.gitignore` — **nikad ne ide u repo**.

## 3. Tajne (Streamlit → Settings → Secrets)

```toml
APP_PASSWORD = "lozinka-koju-pamtis"

# Za upis u CRM preporučen je ZASEBAN testni račun (odvaja Google kvotu od portala).
GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI = '''
{ ... JSON testnog servisnog računa ... }
'''
# Dijeljeni račun — koristi se za bazu zadataka (čitanje).
GOOGLE_SERVICE_ACCOUNT_JSON = '''
{ ... JSON dijeljenog servisnog računa ... }
'''

SHEET_ID = "ID baze zadataka (caki-baza-zadataka)"
CRM_SHEET_ID = "ID Sheeta CAKI CRM — Prijave i baza"
```

| Ključ | Obavezno | Što radi |
|---|---|---|
| `APP_PASSWORD` | ✅ | lozinka za ulazak (bez nje app ne radi — namjerno) |
| `CRM_SHEET_ID` | ✅ | Sheet u koji idu testovi, dodjele, pokušaji, ocjene |
| `SHEET_ID` | ✅ | baza zadataka (20.000+ zadataka) — **samo čitanje** |
| `GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI` | ⭐ | poželjno: upis u CRM ide kroz zaseban račun |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ✅ | dijeljeni račun (baza zadataka) |
| `V2_UPIS` | — | `"da"` ako želiš upis uključen bez klikanja prekidača |

**Koje tajne aplikacija traži i kojim redom** (v. `veza.py`):

| Sheet | Prvo | Ako nema |
|---|---|---|
| CRM (upis) | `GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI` | `GOOGLE_SERVICE_ACCOUNT_JSON` |
| Baza (čitanje) | `GOOGLE_SERVICE_ACCOUNT_JSON` | `GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI` |

> Servisni račun treba **Editor** na CRM Sheetu (upis testova) i **čitanje** baze zadataka.

## 4. Prvi ulazak — redom

1. **Lozinka** → ulaz.
2. Bočna traka → vidi **„Upis je ISKLJUČEN"** ✅ *(tako i treba prvi put)*.
3. **⚙️ Postavke** → mora pisati **„🎬 Stupac `video_url` postoji u bazi"** — to dokazuje da čita
   pravu bazu i da video ne treba dodavati.
4. Kad se uvjeriš da sve čita → uključi **upis** u bočnoj traci → **⚙️ Postavke** →
   **🔧 Pripremi tabove** + kvačica potvrde. To stvara **samo nove** tabove, ništa ne briše.
5. **🧪 Testovi** → sastavi prvi test → **💾 Spremi kao nacrt** → **👥 Objavi**.

## 5. Sigurnosne kočnice (namjerno)

| Kočnica | Zašto |
|---|---|
| Upis **isključen** dok se ne uključi | aplikacija radi na **živoj** bazi (pravi CRM) |
| Baza zadataka se **ne mijenja** nikad | sustav iz nje samo čita |
| „Pripremi tabove" traži potvrdu | stvara tabove u živom Sheetu |
| `.gitignore` blokira `secrets.toml` i `__pycache__` | tajne i smeće ne ulaze u repo |
| Aplikacija je **javna** na Streamlit Cloudu, ali **zaključana lozinkom** | Community Cloud daje samo 1 privatnu app; naša je zaštićena `APP_PASSWORD`-om |

## 6. Ako nešto ne radi

| Simptom | Što provjeriti |
|---|---|
| „U Secrets nedostaje `APP_PASSWORD`" | dodaj ključ u Secrets |
| „nije ispravan JSON … **Nađeno:** pametni navodnici" | kopiraj JSON iz aplikacije koja radi; ne iz Worda/Docsa |
| „`'dict' object has no attribute 'module'`" | bio je bug do 25.10. — treba `veza.py` s `service_account_from_dict` |
| Prazna baza / 0 zadataka | `SHEET_ID` i dijeljenje Sheeta s računom |
| Gumbi za upis ne rade | uključi upis u bočnoj traci |

---

📌 Detalji: `UPDATE_25-10_fazaA_temelj.md` · arhitektura: `ARHITEKTURA.md` · povijest: `DNEVNIK.md`
