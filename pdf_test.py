"""
CAKI testovi v2 — `pdf_test.py`
📄 PDF TESTA — pisana provjera spremna za ispis (Cakijeva napomena 26.10.2026.: „nedostaje
generiranje PDF testa").

Sadržaj: zaglavlje s nazivom firme · naslov testa · datum · uputa · zadaci s **formulama i slikama**
· mjesto za računanje · po izboru **rješenja na kraju**.

Font: isti kao izvještaj (`fontovi/DejaVuSans.ttf` ako postoji, inače Vera uz reportlab) — pa
hrvatska slova i matematika rade. Formule se pišu kao tekst iz baze (`$…$` se skida), jer pravi
LaTeX renderer traži dodatni paket koji nije u projektu — a za ispis je čitljivo i ovako.
"""
from __future__ import annotations

import io
import os

import brend
import model

NAZIV = "CakiSans"
NAZIV_BOLD = "CakiSans-Bold"


def _izvor_fonta() -> tuple:
    obicni, bold = brend.font_putanje()
    if obicni:
        return str(obicni), (str(bold) if bold else ""), "DejaVuSans (repo)"
    try:
        import reportlab
    except Exception:                                  # noqa: BLE001
        return "", "", "nema reportlaba"
    mapa = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    return os.path.join(mapa, "Vera.ttf"), os.path.join(mapa, "VeraBd.ttf"), "Vera (uz reportlab)"


def _registriraj() -> tuple[bool, str]:
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception:                                  # noqa: BLE001
        return False, "reportlab nije instaliran."
    obicni, bold, opis = _izvor_fonta()
    if not obicni or not os.path.exists(obicni):
        return False, "Font za PDF nije nađen."
    try:
        if NAZIV not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(NAZIV, obicni))
        if bold and os.path.exists(bold) and NAZIV_BOLD not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(NAZIV_BOLD, bold))
        elif NAZIV_BOLD not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(NAZIV_BOLD, obicni))
        return True, opis
    except Exception as e:                             # noqa: BLE001
        return False, f"Font se ne može registrirati: {type(e).__name__}."


def _cisti_tekst(tekst) -> str:
    """LaTeX iz baze → čitljiv tekst za ispis (bez $, \\(, \\frac…)."""
    s = model.tekst(tekst)
    for par in (("$", ""), ("\\(", ""), ("\\)", ""), ("\\[", ""), ("\\]", ""), ("\\;", " "),
                ("\\,", " "), ("\\left", ""), ("\\right", ""), ("\\cdot", "·"),
                ("\\times", "×"), ("\\div", ":"), ("\\pm", "±"), ("\\leq", "≤"), ("\\geq", "≥"),
                ("\\neq", "≠"), ("\\pi", "π"), ("\\alpha", "α"), ("\\beta", "β")):
        s = s.replace(par[0], par[1])
    # \frac{a}{b} → (a)/(b)
    for _ in range(6):
        i = s.find("\\frac")
        if i < 0:
            break
        try:
            a_start = s.index("{", i) + 1
            a_kraj = s.index("}", a_start)
            b_start = s.index("{", a_kraj) + 1
            b_kraj = s.index("}", b_start)
            s = s[:i] + "(" + s[a_start:a_kraj] + ")/(" + s[b_start:b_kraj] + ")" + s[b_kraj + 1:]
        except ValueError:
            break
    s = s.replace("\\sqrt", "√").replace("^{2}", "²").replace("^{3}", "³")
    return " ".join(s.split())


def ime_datoteke(naziv: str) -> str:
    ime = model.tekst(naziv) or "test"
    for lose, dobro in {"č": "c", "ć": "c", "ž": "z", "š": "s", "đ": "d",
                        "Č": "C", "Ć": "C", "Ž": "Z", "Š": "S", "Đ": "D"}.items():
        ime = ime.replace(lose, dobro)
    ocisceno = "".join(z if (z.isalnum() or z in "-_") else "_" for z in ime)
    return (ocisceno or "test") + ".pdf"


def generiraj(*, naziv: str, zadaci: list[dict], datum: str = "", ukljuci_rjesenja: bool = False,
              uputa: str = "", podaci_brenda: dict | None = None) -> bytes:
    """Vrati PDF testa. Baca `RuntimeError` ako font ne radi."""
    uspjelo, poruka = _registriraj()
    if not uspjelo:
        raise RuntimeError(poruka)
    if not model.tekst(naziv):
        raise RuntimeError("Test nema naziv — PDF se ne može generirati.")
    if not zadaci:
        raise RuntimeError("Nema odabranih zadataka.")

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer)

    b = podaci_brenda or brend.ucitaj()
    boja = colors.HexColor(b.get("boja") or "#1f4e79")

    naslov_stil = ParagraphStyle("naslov", fontName=NAZIV_BOLD, fontSize=15, leading=19)
    meta = ParagraphStyle("meta", fontName=NAZIV, fontSize=9, leading=12,
                          textColor=colors.HexColor("#555555"))
    zadatak_stil = ParagraphStyle("zadatak", fontName=NAZIV, fontSize=10.5, leading=14.5,
                                  spaceAfter=3)
    broj_stil = ParagraphStyle("broj", fontName=NAZIV_BOLD, fontSize=10.5, leading=14.5,
                               textColor=boja, spaceAfter=2)
    opcija_stil = ParagraphStyle("opcija", fontName=NAZIV, fontSize=10, leading=13.5, leftIndent=8)
    rjesenje_stil = ParagraphStyle("rjesenje", fontName=NAZIV, fontSize=9.5, leading=13)
    odjeljak = ParagraphStyle("odjeljak", fontName=NAZIV_BOLD, fontSize=11, leading=14,
                              spaceBefore=8, spaceAfter=4, textColor=boja)

    tok = [Paragraph(model.tekst(b.get("naziv")), naslov_stil),
           Paragraph(model.tekst(b.get("slogan")), meta), Spacer(1, 3 * mm),
           Paragraph(model.tekst(naziv), ParagraphStyle(
               "ime", fontName=NAZIV_BOLD, fontSize=13, leading=17, spaceAfter=2))]

    podnaslov = " · ".join(x for x in (model.tekst(datum) or model.sada().strftime("%d.%m.%Y."),
                                       f"{len(zadaci)} zadataka",
                                       f"{sum(model.broj(z.get('bodovi'), 1) for z in zadaci):g} bodova")
                           if x)
    tok += [Paragraph(podnaslov, meta), Spacer(1, 2 * mm)]
    tok += [Paragraph("Ime i prezime: ______________________________________    "
                      "Bodovi: ______ / ______", ParagraphStyle(
                          "imepolje", fontName=NAZIV, fontSize=10, leading=16))]
    tok += [Spacer(1, 2 * mm)]
    if model.tekst(uputa):
        tok += [Paragraph(model.tekst(uputa), meta), Spacer(1, 2 * mm)]
    tok += [Paragraph("_" * 96, meta), Spacer(1, 2 * mm)]

    for i, z in enumerate(zadaci, start=1):
        dijelovi = [Paragraph(f"Zadatak {i}. ({model.broj(z.get('bodovi'), 1):g} bod.)", broj_stil),
                    Paragraph(_cisti_tekst(z.get("tekst")), zadatak_stil)]
        slika = model.tekst(z.get("slika"))
        if slika:
            put = _put_do_slike(slika)
            if put:
                try:
                    dijelovi.append(Image(str(put), width=70 * mm, height=45 * mm,
                                          kind="proportional"))
                    dijelovi.append(Spacer(1, 2 * mm))
                except Exception:                      # noqa: BLE001 — loša slika ne ruši test
                    dijelovi.append(Paragraph(f"[slika: {slika}]", meta))
            else:
                dijelovi.append(Paragraph(f"[slika: {slika}]", meta))
        for j, opcija in enumerate(z.get("opcije") or []):
            slovo = chr(65 + j)
            dijelovi.append(Paragraph(f"{slovo}) {_cisti_tekst(opcija)}", opcija_stil))
        if not (z.get("opcije") or []):
            dijelovi.append(Spacer(1, 8 * mm))         # mjesto za računanje
        dijelovi.append(Spacer(1, 3 * mm))
        tok.append(KeepTogether(dijelovi))

    if ukljuci_rjesenja:
        tok += [Paragraph("Rješenja", odjeljak)]
        for i, z in enumerate(zadaci, start=1):
            tok.append(Paragraph(f"{i}. {_cisti_tekst(z.get('odgovor')) or '—'}", rjesenje_stil))

    kontakt = brend.kontakt_redak(b)

    def _podnozje(canvas, dokument):
        canvas.saveState()
        canvas.setFont(NAZIV, 7.5)
        canvas.setFillColor(colors.HexColor("#777777"))
        if kontakt:
            canvas.drawCentredString(A4[0] / 2, 11 * mm, kontakt)
        canvas.setFont(NAZIV, 7.5)
        canvas.drawRightString(A4[0] - 18 * mm, 11 * mm, f"strana {dokument.page}")
        canvas.restoreState()

    meduspremnik = io.BytesIO()
    dokument = SimpleDocTemplate(meduspremnik, pagesize=A4,
                                 leftMargin=18 * mm, rightMargin=18 * mm,
                                 topMargin=16 * mm, bottomMargin=22 * mm,
                                 title=model.tekst(naziv),
                                 author=model.tekst(b.get("naziv")))
    dokument.build(tok, onFirstPage=_podnozje, onLaterPages=_podnozje)
    return meduspremnik.getvalue()


def _put_do_slike(naziv: str):
    """Lokalna slika zadatka (ako je u repou); inače None — u PDF ide napomena."""
    from pathlib import Path

    for mapa in (Path(__file__).resolve().parent / "slike",
                 Path(__file__).resolve().parent):
        put = mapa / model.tekst(naziv)
        if put.exists():
            return put
    return None


def prikazi_preuzimanje(st, *, naziv: str, zadaci: list[dict], datum: str = "",
                        ukljuci_rjesenja: bool = False, uputa: str = "", kljuc: str = "") -> None:
    """Gumb za PDF testa; greška ne ruši stranicu."""
    try:
        sadrzaj = generiraj(naziv=naziv, zadaci=zadaci, datum=datum,
                            ukljuci_rjesenja=ukljuci_rjesenja, uputa=uputa,
                            podaci_brenda=brend.ucitaj(st.secrets))
    except Exception as e:                             # noqa: BLE001
        st.caption(f"PDF testa se ne može generirati: {e}")
        return
    st.download_button(
        "📄 Generiraj PDF testa",
        data=sadrzaj,
        file_name=ime_datoteke(naziv),
        mime="application/pdf",
        key="v2_pdftest_" + (kljuc or model.tekst(naziv)[:20] or "x"),
    )
