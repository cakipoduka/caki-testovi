# 🔎 Preostalo iz starog buildera — što još preuzeti

Prošao sam **sve funkcije** `2_test_builder.py` (43 funkcije) i usporedio s v2. Ovo je ono što još
nije preuzeto, po vrijednosti.

## ✅ Upravo preuzeto (26.10.2026., Kladova lekcija)

| Stari kod | Zašto je bitno |
|---|---|
| **`prikazi_sliku_html`** + `_slika_html_za` | `st.image()` **dekodira sliku na serveru** — Pillow/libpng/libjpeg su 15.9. i 14.10.2026. **srušili cijeli proces**. Rješenje: `<img src="data:...">`, dekodira **preglednik**. Sada i v2 tako radi (`slike_zadataka.prikazi_sliku_html`). |
| **`slika_valjana_za_prikaz`** | provjera zaglavlja datoteke prije prikaza/PDF-a |

## ⛔ Još nije preuzeto — po vrijednosti

| # | Stari kod (funkcija, linija) | Što daje | Trud |
|---|---|---|---|
| 1 | **`skupine_zadataka.py`** (18 KB) + `dodaj_jedinicu`, `izgradi_stavke_blok`, `izgradi_rjesenja_blok` | **skupine zadataka** (uvod + stavke a), b), c)) — v2 ih uopće nema; bez toga neki zadaci iz baze ne mogu u test | **velik** |
| 2 | `_spremi_nacrt` L1178, `init_draft_ws`, `_stanje_za_spremanje` L354, `_ucitaj_stanje` L366 | **autosave nacrta** — „nikad ne smije prekinuti profesorov rad” (22.10.) | srednji |
| 3 | `init_predlosci_ws` L337, predlošci (15×) | **predlošci testova** — spremi/učitaj gotov odabir | srednji |
| 4 | `pomakni` L550, `ukloni` L557 (UI L1044–1050) | **redoslijed ↑↓** i uklanjanje u panelu odabranih | mali |
| 5 | `prikazi_opcije` (8×, L61/508/790/853/959) | **isključi ponuđene odgovore** za pojedini zadatak | mali |
| 6 | Bloom (L31, L979) | **Bloom razina** u panelu (5 razina, „nije označeno → preskače se u analizi”) | mali |
| 7 | `procjena` stranica L1140 | gruba **procjena broja stranica** prije PDF-a | mali |
| 8 | `predmet_config.postavke(...)["zaglavlje_pdf"]` | zaglavlje PDF-a po predmetu (sada fiksno `MATEMATIKA`) | mali |
| 9 | `mamac` (L1221–1227) | dodatak **„ništa od navedenog”** svim višestrukim zadacima | mali |

## Što je VEĆ preuzeto (za kontrolu)

`escape_outside_math` · `_escape_plain_segment` · `SPECIAL_CHARS` · `broj_dolara` ·
`pronadji_neuparene_dolare` · `formatiraj_opciju` · `izgradi_opcije_blok` · `izgradi_kategorije_tex` ·
`izgradi_kategorije_redovi` · `broj_iz_stringa` · `provjeri_zbroj_kategorija` · `KATEGORIJE_INFO` ·
`razdvoji_slike` · `slika_valjana_za_prikaz` (provjera zaglavlja) · **PDF pipeline** (predložak, stil,
dva prolaza pdflatexa, log) · `prikazi_sliku_html` (novo).

## Redoslijed kojim bih radio

1. **Panel odabranih** (točke 4, 5, 6, 9) — jedan zahvat, vidi se odmah, mali rizik.
2. **Predlošci** (3) — najveća ušteda vremena Cakiju.
3. **Autosave nacrta** (2).
4. **Skupine zadataka** (1) — najveći zahvat, na kraju.

> Pravilo ostaje: **prvo pročitaj stari kod, pa piši** — i u izvještaju napiši što je preuzeto.
