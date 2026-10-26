"""
CAKI testovi v2 — `tex_test.py`
📄 PDF TESTA preko **LaTeX-a (pdflatex)** — isti pipeline kao stari Test Builder.

ISPRAVAK 26.10.2026.: Caki je upozorio da PDF generator **već postoji** i koristi se svaki dan.
Bio je u pravu — stari builder gradi `main.tex` iz predloška + `caki-style.sty`, ubacuje zadatke
kroz `\\zadatakbod{...}` i pokreće `pdflatex` dva puta. Zato se ovdje **preuzima isti pipeline**,
a ne izmišlja novi: formule se stvarno slikaju, a izgled je isti kao do sada (stilovi iz
`caki-style.sty`).

PREUZETO iz `caki-baza-zadataka/pages/2_test_builder.py` (nepromijenjeno):
    `_escape_plain_segment`, `escape_outside_math`, `izgradi_kategorije_tex`, `formatiraj_opciju`,
    `izgradi_opcije_blok`, `broj_iz_stringa`, `izgradi_kategorije_redovi`,
    `pronadji_neuparene_dolare` + konstante `SPECIAL_CHARS`, `KOMBINIRAJUCA_TOCKA_IZNAD`.

NOVO za v2:
    `popuni_predlozak()` — sve placeholdere zamijeni (bez toga pdflatex pada),
    `izgradi_tex()` — tijelo iz zamrznutog oblika zadatka (`tekst`, `opcije`, `slika`, `bodovi`),
    `generiraj()` — mapa, dva prolaza pdflatexa, jasna greška s logom (nikad pad cijele aplikacije).

Ugledanje na stari ugovor predloška:
    \\cakiispithead{ NASLOV }{ DATUM }{ TIP }{ UKUPNO_BODOVA }{ KATEGORIJE_REDOVI }
    \\input{generated/zadaci_body} · \\krajtesta{ KRAJ_OZNAKA } · rješenja (opcionalno)
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile

import model

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tex")
TIP_DOKUMENTA = ("Pisana provjera znanja", "Zadaci za vježbu na satu", "Domaća zadaća")
KRAJ_OZNAKA = {
    "Pisana provjera znanja": "KRAJ TESTA",
    "Zadaci za vježbu na satu": "KRAJ ZADATAKA ZA VJEŽBU",
    "Domaća zadaća": "KRAJ DOMAĆE ZADAĆE",
}


SPECIAL_CHARS = {
    "\\": r"\textbackslash{}",
    "&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}

KOMBINIRAJUCA_TOCKA_IZNAD = "̇"

def _escape_plain_segment(segment: str) -> str:
    """Escapira SPECIAL_CHARS znak-po-znak kao dosad, ali PRIJE toga izdvaja
    parove (bilo koji znak + KOMBINIRAJUCA_TOCKA_IZNAD) u already-LaTeX
    "$\\dot{znak}$" komad koji se NE escapira (mora ostati literalan LaTeX)."""
    if KOMBINIRAJUCA_TOCKA_IZNAD not in segment:
        return "".join(SPECIAL_CHARS.get(ch, ch) for ch in segment)
    komadi = re.split(r"(.̇)", segment)
    out = []
    for komad in komadi:
        if len(komad) == 2 and komad[1] == KOMBINIRAJUCA_TOCKA_IZNAD:
            out.append(f"$\\dot{{{komad[0]}}}$")
        else:
            out.append("".join(SPECIAL_CHARS.get(ch, ch) for ch in komad))
    return "".join(out)

def escape_outside_math(text: str) -> str:
    if not text:
        return ""
    parts = re.split(r"(\$[^$]*\$)", text)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
        else:
            out.append(_escape_plain_segment(part))
    return "".join(out)

def izgradi_kategorije_tex(kategorije: dict) -> str:
    """kategorije: {"UZV": "2", "RP": "1", ...} -> LaTeX tekst prikazan kao mala
    oznaka na vrhu okvira zadatka u PDF-u, npr. "UZV: 2 bod.  RP: 1 bod."
    Redoslijed je UVIJEK UZV/RP/MK (fiksiran u KATEGORIJE_INFO), bez obzira
    kojim je redom profesor čekirao kategorije u sučelju. Ako je kategorija
    čekirana ali bodovi nisu upisani, prikazuje se samo kod kategorije."""
    dijelovi = []
    for kod, _naziv in KATEGORIJE_INFO:
        if kod not in kategorije:
            continue
        bod = str(kategorije.get(kod, "")).strip()
        if bod:
            dijelovi.append(f"{kod}: {escape_outside_math(bod)}\\space bod.")
        else:
            dijelovi.append(kod)
    return "\\quad ".join(dijelovi)

def formatiraj_opciju(opcija):
    """Baza sprema ponudjeni_odgovori kao ČIST LaTeX BEZ $...$ omotača kad je
    opcija matematika (npr. "\\frac{1}{(2 a-1)^{3}}") - PreTeXt build ih sam
    omata. Ali OPREZ: neke opcije su čist tekst bez ikakve matematike (npr.
    "trostrana piramida" kod zadataka o geometrijskim tijelima) - te NE SMIJU
    u $...$, jer LaTeX matematički način rada IGNORIRA razmake među riječima
    (postalo bi "trostranapiramida", bez razmaka - stvarni bug koji smo vidjeli).

    Razlikovanje: ako opcija sadrži LaTeX naredbu ili math-specifičan znak
    (\\, ^, _) → tretiramo kao čistu matematiku, omatamo u $...$ BEZ escapiranja
    (escapiranje bi razbilo \\frac{...}). Inače → čist tekst, ide kroz
    escape_outside_math (čuva razmake, escapira posebne znakove poput %/&)."""
    opcija = opcija.strip()
    if "$" in opcija:
        # Već ima $ (npr. profesor ručno upisao "$x=1$" u ad-hoc polje po
        # uputi u sučelju) - slobodan tekst s ugrađenom matematikom.
        return escape_outside_math(opcija)
    if re.search(r"[\\^_]", opcija):
        # Sadrži LaTeX naredbu (\frac, \sqrt...) ili ^ / _ - čista matematika.
        return f"${opcija}$"
    # Obični tekst bez ikakve matematike - NE omatati u $...$.
    return escape_outside_math(opcija)

def izgradi_opcije_blok(ponudjeni_odgovori):
    """Gradi LaTeX za prikaz ponuđenih odgovora (A/B/C/D...) ispod teksta zadatka,
    kao PRIRODAN tok teksta (ne fiksna tablica/popis) - LaTeX sam odlučuje hoće
    li sve stati u jedan redak (kompaktno, štedi papir) ili prelomiti na više
    redaka. Radi za BILO KOJI broj opcija (2, 3, 4, 5, 6+) - važno jer dodatak
    "Ništa od navedenog" (vidi dodaj_nista_od_navedenog niže) može gurnuti
    zadatak koji je već imao 5 opcija na 6.
    VAŽNO: ovaj blok se NE smije propuštati kroz escape_outside_math kao cjelina -
    dodaje se NAKON escapiranja teksta zadatka, jer sadrži prave LaTeX naredbe
    (\\textbf, \\quad...), a ne slobodni tekst profesora. Svaka POJEDINA opcija
    se obrađuje zasebno preko formatiraj_opciju() (vidi gore)."""
    slova = ["A", "B", "C", "D", "E", "F", "G", "H"]
    opcije = [formatiraj_opciju(o) for o in ponudjeni_odgovori if o.strip()]
    if not opcije:
        return ""
    dijelovi = [f"\\textbf{{{slova[j]})}}~{opc}" for j, opc in enumerate(opcije)]
    return "\n\\par\\vspace{3mm}\n\\noindent " + "\\quad ".join(dijelovi) + "\\par"

def broj_iz_stringa(vrijednost) -> float:
    """Parsira tekstualni unos bodova (dopušta i ',' kao decimalni zarez) u float.
    Baca ValueError za prazno/neispravno - poziv MORA to hvatati (koristi se i u
    UI upozorenju i u blokirajućoj provjeri prije generiranja)."""
    return float(str(vrijednost).strip().replace(",", "."))

def izgradi_kategorije_redovi(ukupno_po_kategoriji: dict) -> str:
    """ukupno_po_kategoriji: {"UZV": 3.0, "RP": 1.0, ...} (zbroj bodova te
    kategorije preko SVIH odabranih zadataka) -> LaTeX blok redaka za zaglavlje
    testa (\\cakiispithead #5) - PO JEDAN redak s "Ostvareno"/"Ocjena" za SVAKU
    kategoriju koja se stvarno koristi u testu (test se ocjenjuje po kategoriji,
    ne jednim cjelokupnim zbrojem/ocjenom - vidi #25 u CAKI_MASTER_BAZA).
    Kategorije bez ijednog dodijeljenog boda (0 ili nema u dictu) se preskaču."""
    redovi = []
    for kod, _naziv in KATEGORIJE_INFO:
        total = ukupno_po_kategoriji.get(kod) or 0
        if not total:
            continue
        total_str = f"{total:g}"
        redovi.append(
            "\\par\\vspace{2mm}\n"
            f"\\noindent\\textbf{{{kod} \\textemdash{{}} ukupno bodova:}} {total_str} \\quad "
            "\\textbf{Ostvareno:} \\makebox[2cm]{\\hrulefill} \\quad "
            "\\textbf{Ocjena:} \\makebox[2cm]{\\hrulefill}"
        )
    return "".join(redovi)

def pronadji_neuparene_dolare(zadaci_odabrani):
    """Vraća listu (index, opis, polje, tekst) za zadatke gdje BILO KOJE polje
    koje ide u LaTeX (tekst, rješenje, konačan odgovor, ponuđene opcije) ima
    neparan broj $ znakova - najčešći uzrok pucanja kompajliranja."""
    problemi = []
    for i, z in enumerate(zadaci_odabrani, start=1):
        zid = z.get("id") or "ručni zadatak"
        polja_za_provjeru = [
            ("tekst zadatka", z.get("tekst", "")),
            ("rješenje", z.get("rjesenje", "")),
            ("konačan odgovor", z.get("konacan_odgovor", "")),
        ]
        for j, opcija in enumerate(z.get("ponudjeni_odgovori") or []):
            slovo = ["A", "B", "C", "D", "E", "F", "G", "H"][j] if j < 8 else str(j + 1)
            polja_za_provjeru.append((f"opcija {slovo}", opcija))
        for naziv_polja, sadrzaj in polja_za_provjeru:
            if broj_dolara(sadrzaj) % 2 != 0:
                problemi.append((i, zid, naziv_polja, sadrzaj))
        if z.get("stavke"):
            for oznaka, polje, sadrzaj in sve_stavke_dolari_neuparene(z["stavke"], broj_dolara):
                problemi.append((i, zid, f"stavka {oznaka} ({polje})", sadrzaj))
    return problemi



KATEGORIJE_INFO = [
    ("UZV", "Usvojenost znanja i vještina"),
    ("RP", "Rješavanje problema"),
    ("MK", "Matematička komunikacija"),
]

# ------------------------------------------------------------------ tijelo zadataka (v2 oblik)

def izgradi_tex(zadaci, ukljuci_rjesenja: bool = False, dodaj_mamac: bool = False,
                mamac_tekst: str = "") -> tuple[str, str]:
    """Vrati (zadaci_body, rjesenja_body) — točno ono što `main.tex` uvozi."""
    zad_lines, rjes_lines = [], []
    for i, z in enumerate(zadaci or [], start=1):
        tekst = escape_outside_math(model.tekst(z.get("tekst")).strip())
        video = model.tekst(z.get("video_url")).strip()
        bodovi = f"{model.broj(z.get('bodovi'), 1):g}"
        tip_z = model.tekst(z.get("tip"))
        kategorije_tex = izgradi_kategorije_tex({})

        opcije = [model.tekst(o) for o in (z.get("opcije") or []) if model.tekst(o)]
        if opcije:
            if dodaj_mamac and model.tekst(mamac_tekst):
                opcije = opcije + [model.tekst(mamac_tekst)]
            tekst += izgradi_opcije_blok(opcije)

        slike = [model.tekst(z.get("slika"))] if model.tekst(z.get("slika")) else []
        slika_rel = ",".join("images/" + x for x in slike)
        zad_lines.append(
            r"\zadatakbod{" + tekst + "}{" + video + "}{" + bodovi + "}{" + slika_rel + "}{"
            + tip_z + "}{" + kategorije_tex + "}")
        zad_lines.append("")

        if ukljuci_rjesenja:
            konacan = escape_outside_math(model.tekst(z.get("odgovor")))
            rjes_lines.append(r"\rjesenje{" + str(i) + r"}{\textit{Puni postupak nije unesen u bazu.}}{"
                              + konacan + "}")
            rjes_lines.append("")
    return "\n".join(zad_lines), "\n".join(rjes_lines)


def _upozorenja(zadaci) -> list[str]:
    """Prije kompajliranja: neupareni `$` i prazni zadaci — najčešći uzroci pada pdflatexa."""
    problemi = []
    for i, z in enumerate(zadaci or [], start=1):
        tekst = model.tekst(z.get("tekst"))
        if tekst.count("$") % 2:
            problemi.append(f"Zadatak {i} ({model.tekst(z.get('id'))}): neuparen `$` u tekstu.")
        if not tekst.strip():
            problemi.append(f"Zadatak {i}: prazan tekst.")
    return problemi


# ------------------------------------------------------------------ predložak

def popuni_predlozak(*, naziv: str, datum: str, tip: str = TIP_DOKUMENTA[0],
                     ukupno_bodova="", kategorije_redovi: str = "",
                     predmet_zaglavlje: str = "MATEMATIKA",
                     rjesenja_sekcija: str = "") -> str:
    """Zamijeni SVE placeholdere predloška — bez toga bi `\\cakiispithead` dobio `{{NASLOV}}`."""
    with open(os.path.join(TEMPLATE_DIR, "main.tex"), encoding="utf-8") as f:
        main_tex = f.read()
    kraj = KRAJ_OZNAKA.get(tip, "KRAJ TESTA")
    zamjene = {
        "{{NASLOV}}": escape_outside_math(naziv),
        "{{DATUM}}": datum,
        "{{TIP}}": tip,
        "{{UKUPNO_BODOVA}}": model.tekst(ukupno_bodova) or f"{model.broj(ukupno_bodova):g}",
        "{{KATEGORIJE_REDOVI}}": kategorije_redovi,
        "{{KRAJ_OZNAKA}}": kraj,
        "{{PREDMET_ZAGLAVLJE}}": predmet_zaglavlje,
        "{{RJESENJA_SEKCIJA}}": rjesenja_sekcija,
    }
    for kljuc, vrijednost in zamjene.items():
        main_tex = main_tex.replace(kljuc, str(vrijednost))
    ostali = [k for k in ("{{NASLOV}}", "{{DATUM}}", "{{TIP}}", "{{UKUPNO_BODOVA}}",
                          "{{KATEGORIJE_REDOVI}}", "{{KRAJ_OZNAKA}}", "{{PREDMET_ZAGLAVLJE}}",
                          "{{RJESENJA_SEKCIJA}}") if k in main_tex]
    if ostali:
        raise RuntimeError("Predložak nije potpuno popunjen: " + ", ".join(ostali))
    return main_tex


# ------------------------------------------------------------------ kompajliranje

def ima_pdflatex() -> bool:
    return shutil.which("pdflatex") is not None


def ime_datoteke(naziv: str) -> str:
    ime = model.tekst(naziv) or "test"
    for lose, dobro in {"č": "c", "ć": "c", "ž": "z", "š": "s", "đ": "d",
                        "Č": "C", "Ć": "C", "Ž": "Z", "Š": "S", "Đ": "D"}.items():
        ime = ime.replace(lose, dobro)
    return "".join(z if (z.isalnum() or z in "-_") else "_" for z in ime) + ".pdf"


def generiraj(*, naziv: str, zadaci: list, datum: str = "", tip: str = TIP_DOKUMENTA[0],
              ukljuci_rjesenja: bool = False, slike: dict | None = None,
              dodaj_mamac: bool = False, mamac_tekst: str = "",
              predmet_zaglavlje: str = "MATEMATIKA", timeout: int = 90) -> bytes:
    """Složi i kompajliraj PDF. Baca `RuntimeError` s logom (pozivatelj je uhvati i pokaže)."""
    if not model.tekst(naziv):
        raise RuntimeError("Test nema naziv — PDF se ne može generirati.")
    if not zadaci:
        raise RuntimeError("Nema odabranih zadataka.")
    problemi = _upozorenja(zadaci)
    if problemi:
        raise RuntimeError("Prije kompajliranja: " + " ".join(problemi))
    if not ima_pdflatex():
        raise RuntimeError("pdflatex nije instaliran u ovoj okolini "
                           "(na Streamlit Cloudu se instalira iz `packages.txt`).")

    zadaci_body, rjesenja_body = izgradi_tex(zadaci, ukljuci_rjesenja, dodaj_mamac, mamac_tekst)
    ukupno = sum(model.broj(z.get("bodovi"), 1) for z in zadaci)
    main_tex = popuni_predlozak(
        naziv=naziv,
        datum=model.tekst(datum) or model.sada().strftime("%d.%m.%Y."),
        tip=tip,
        ukupno_bodova=f"{ukupno:g}",
        predmet_zaglavlje=predmet_zaglavlje,
        rjesenja_sekcija=(r"\input{generated/rjesenja_body}" if ukljuci_rjesenja else ""),
    )

    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "generated"), exist_ok=True)
        os.makedirs(os.path.join(tmp, "images"), exist_ok=True)
        with open(os.path.join(tmp, "main.tex"), "w", encoding="utf-8") as f:
            f.write(main_tex)
        shutil.copy2(os.path.join(TEMPLATE_DIR, "caki-style.sty"),
                     os.path.join(tmp, "caki-style.sty"))
        with open(os.path.join(tmp, "generated", "zadaci_body.tex"), "w", encoding="utf-8") as f:
            f.write(zadaci_body)
        with open(os.path.join(tmp, "generated", "rjesenja_body.tex"), "w", encoding="utf-8") as f:
            f.write(rjesenja_body)
        for ime, bajtovi in (slike or {}).items():
            if bajtovi and ime:
                with open(os.path.join(tmp, "images", ime), "wb") as f:
                    f.write(bajtovi)

        for _ in range(2):                                  # dva prolaza (kao stari builder)
            rezultat = subprocess.run(
                ["pdflatex", "-no-shell-escape", "-interaction=nonstopmode",
                 "-halt-on-error", "main.tex"],
                cwd=tmp, capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace")
            if rezultat.returncode != 0:
                log = "\n".join((rezultat.stdout or "").splitlines()[-40:])
                raise RuntimeError("Kompajliranje nije uspjelo.\n" + log)
        with open(os.path.join(tmp, "main.pdf"), "rb") as f:
            return f.read()


def prikazi_preuzimanje(st, *, naziv: str, zadaci: list, datum: str = "",
                        tip: str = TIP_DOKUMENTA[0], ukljuci_rjesenja: bool = False,
                        slike: dict | None = None, kljuc: str = "") -> None:
    """Gumb za PDF testa. Greška se prikaže kao poruka — aplikacija se ne ruši."""
    try:
        sadrzaj = generiraj(naziv=naziv, zadaci=zadaci, datum=datum, tip=tip,
                            ukljuci_rjesenja=ukljuci_rjesenja, slike=slike)
    except Exception as e:                                  # noqa: BLE001
        st.warning(f"PDF testa se ne može generirati: {e}")
        return
    st.download_button("📄 Generiraj PDF testa", data=sadrzaj, file_name=ime_datoteke(naziv),
                       mime="application/pdf", key="v2_tex_" + (kljuc or "x"))
