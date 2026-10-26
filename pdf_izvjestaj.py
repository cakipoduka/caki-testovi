"""
CAKI testovi v2 — `pdf_izvjestaj.py`
📄 IZVJEŠTAJ ZA RODITELJE — pravi PDF s logotipom, kontaktom i **jezikom bez ocjenjivanja**.

Cakijeva pravila (26.10.2026.):
  · on **ne ocjenjuje** djecu — pomaže im položiti ispit. Zato izvještaj kaže
    **„ostvareni rezultat”** i opisnu razinu, a NE „predlog ocjene”.
  · **logo, web i e-mail idu na svaki izvještaj** — služe kao promocija firme.
  · sve što se mijenja (naziv, slogan, web, e-mail, telefon, boja) je u `brend.py`.

FONT: prvo `fontovi/DejaVuSans.ttf` (ako ga Caki stavi u repo), inače `Vera.ttf` koji dolazi uz
reportlab. `ima_hrvatska_slova()` provjerava pokrivenost prije nego se bilo što pošalje.
"""
from __future__ import annotations

import io
import os

import brend
import model
import zakljucna

NAZIV = "CakiSans"
NAZIV_BOLD = "CakiSans-Bold"


def _izvor_fonta() -> tuple:
    """(obični, bold, opis) — DejaVu iz repoa ako postoji, inače Vera iz reportlaba."""
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
    """Registriraj font. Vraća (uspjelo, poruka)."""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except Exception:                                  # noqa: BLE001
        return False, "reportlab nije instaliran (u deployu jest, iz requirements.txt)."
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


def ima_hrvatska_slova() -> bool:
    """Pokriva li font koji će se koristiti č ć ž š đ?"""
    try:
        from reportlab.pdfbase.ttfonts import TTFont

        obicni, _, _ = _izvor_fonta()
        pokriveno = TTFont("Proba", obicni).face.charToGlyph
        return all(ord(z) in pokriveno for z in "čćžšđČĆŽŠĐ")
    except Exception:                                  # noqa: BLE001
        return False


def font_opis() -> str:
    return _izvor_fonta()[2]


def _postotak(bodovi, maks) -> int:
    b, m = model.broj(bodovi), model.broj(maks)
    return int(round(100 * b / m)) if m else 0


def generiraj(*, ucenik: dict, testovi: list[dict], radovi: list[dict] | None = None,
              napomena: str = "", podaci_brenda: dict | None = None) -> bytes:
    """Vrati PDF. Baca `RuntimeError` s objašnjenjem ako font ne radi."""
    uspjelo, poruka = _registriraj()
    if not uspjelo:
        raise RuntimeError(poruka)

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

    b = podaci_brenda or brend.ucitaj()
    boja = colors.HexColor(b.get("boja") or "#1f4e79")

    ucenik = ucenik or {}
    ime = model.tekst(ucenik.get("ime")) or model.tekst(ucenik.get("ucenik_id")) or "Učenik"
    sifra = model.tekst(ucenik.get("ucenik_id"))
    grupa = model.tekst(ucenik.get("grupa"))
    postoci = [t.get("postotak", _postotak(t.get("bodovi"), t.get("maks"))) for t in (testovi or [])]
    prosjek = int(round(sum(postoci) / len(postoci))) if postoci else 0

    naslov = ParagraphStyle("naslov", fontName=NAZIV_BOLD, fontSize=15, leading=19, spaceAfter=1)
    slogan = ParagraphStyle("slogan", fontName=NAZIV, fontSize=8.5, leading=11,
                            textColor=colors.HexColor("#666666"))
    podnaslov = ParagraphStyle("podnaslov", fontName=NAZIV, fontSize=9, leading=12,
                               textColor=colors.HexColor("#555555"), spaceAfter=8)
    odjeljak = ParagraphStyle("odjeljak", fontName=NAZIV_BOLD, fontSize=11, leading=14,
                              spaceBefore=10, spaceAfter=4, textColor=boja)
    tijelo = ParagraphStyle("tijelo", fontName=NAZIV, fontSize=9.5, leading=13)
    veliko = ParagraphStyle("veliko", fontName=NAZIV_BOLD, fontSize=13, leading=17, spaceAfter=2)

    tok = []
    # --- zaglavlje: logo + naziv + slogan (promocija na svakom izvještaju)
    logo = brend.logo_putanja()
    if logo is not None:
        try:
            slika = Image(str(logo), width=22 * mm, height=22 * mm, kind="proportional")
            zaglavlje = Table([[slika, Paragraph(f"{model.tekst(b.get('naziv'))}", naslov)]],
                              colWidths=[26 * mm, 140 * mm])
            zaglavlje.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
            tok += [zaglavlje]
        except Exception:                              # noqa: BLE001 — loš logo ne ruši PDF
            tok += [Paragraph(model.tekst(b.get("naziv")), naslov)]
    else:
        tok += [Paragraph(model.tekst(b.get("naziv")), naslov)]
    if model.tekst(b.get("slogan")):
        tok += [Paragraph(model.tekst(b.get("slogan")), slogan)]
    tok += [Spacer(1, 4 * mm)]

    tok += [Paragraph(f"Izvještaj — {ime}", ParagraphStyle(
        "ime", fontName=NAZIV_BOLD, fontSize=13, leading=17, spaceAfter=2))]
    meta = f"Šifra: {sifra}"
    if grupa:
        meta += f" · Grupa: {grupa}"
    meta += " · " + model.sada().strftime("%d.%m.%Y.")
    tok += [Paragraph(meta, podnaslov)]

    # --- ostvareni rezultat (NE školska ocjena)
    tok += [Paragraph("Ostvareni rezultat", odjeljak)]
    if postoci:
        tok += [Paragraph(zakljucna.ostvareno(prosjek), veliko),
                Paragraph(f"Iz {len(postoci)} predanih testova. Rezultat pokazuje koliko je "
                          "usvojeno — služi kao putokaz za dalje, ne kao ocjena.", tijelo)]
    else:
        tok += [Paragraph("Nema predanih testova.", tijelo)]

    # --- testovi
    tok += [Paragraph("Testovi", odjeljak)]
    if testovi:
        podaci = [["Test", "Datum", "Bodovi", "Postotak"]]
        for t in testovi:
            p = t.get("postotak", _postotak(t.get("bodovi"), t.get("maks")))
            podaci.append([
                Paragraph(model.tekst(t.get("naziv")) or "—", tijelo),
                model.tekst(t.get("datum")) or "—",
                f"{model.broj(t.get('bodovi')):g} / {model.broj(t.get('maks')):g}",
                f"{p} %",
            ])
        tablica = Table(podaci, colWidths=[75 * mm, 30 * mm, 35 * mm, 30 * mm])
        tablica.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
            ("BACKGROUND", (0, 0), (-1, 0), boja),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), NAZIV_BOLD),
            ("FONTNAME", (0, 1), (-1, -1), NAZIV),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        tok += [tablica]
    else:
        tok += [Paragraph("Nema testova.", tijelo)]

    if radovi:
        tok += [Paragraph("Priloženi radovi", odjeljak)]
        for r in radovi:
            pregled = "pregledano" if model.tekst(r.get("potvrdjeno")) else "čeka pregled"
            tok += [Paragraph(f"• {model.tekst(r.get('naziv')) or 'Rad'} — {pregled}", tijelo)]

    if model.tekst(napomena):
        tok += [Paragraph("Napomena", odjeljak), Paragraph(model.tekst(napomena), tijelo)]

    # --- podnožje na SVAKOJ stranici (web, e-mail, telefon — promocija)
    kontakt = brend.kontakt_redak(b)
    adresa = model.tekst(b.get("adresa"))

    def _podnozje(canvas, dokument):
        canvas.saveState()
        canvas.setFont(NAZIV, 7.5)
        canvas.setFillColor(colors.HexColor("#777777"))
        y = 10 * mm
        if kontakt:
            canvas.drawCentredString(A4[0] / 2, y + 3 * mm, kontakt)
        if adresa:
            canvas.drawCentredString(A4[0] / 2, y - 1 * mm, adresa)
        canvas.setFont(NAZIV_BOLD, 7.5)
        canvas.setFillColor(boja)
        canvas.drawCentredString(A4[0] / 2, y + 7 * mm, model.tekst(b.get("naziv")))
        canvas.restoreState()

    meduspremnik = io.BytesIO()
    dokument = SimpleDocTemplate(meduspremnik, pagesize=A4,
                                 leftMargin=18 * mm, rightMargin=18 * mm,
                                 topMargin=16 * mm, bottomMargin=26 * mm,
                                 title=f"Izvještaj — {ime}", author=model.tekst(b.get("naziv")))
    dokument.build(tok, onFirstPage=_podnozje, onLaterPages=_podnozje)
    return meduspremnik.getvalue()


def ime_datoteke(ucenik: dict) -> str:
    ime = model.tekst((ucenik or {}).get("ime")) or model.tekst((ucenik or {}).get("ucenik_id")) \
        or "ucenik"
    for lose, dobro in {"č": "c", "ć": "c", "ž": "z", "š": "s", "đ": "d",
                        "Č": "C", "Ć": "C", "Ž": "Z", "Š": "S", "Đ": "D"}.items():
        ime = ime.replace(lose, dobro)
    ocisceno = "".join(z if (z.isalnum() or z in "-_") else "_" for z in ime)
    return (ocisceno or "ucenik") + "_izvjestaj.pdf"


def prikazi_preuzimanje(st, *, ucenik: dict, testovi: list[dict], radovi=None,
                        napomena: str = "", kljuc: str = "") -> None:
    """Gumb za PDF. Ako font/reportlab ne rade, ne ruši stranicu — kaže zašto i nudi HTML."""
    try:
        sadrzaj = generiraj(ucenik=ucenik, testovi=testovi, radovi=radovi, napomena=napomena,
                            podaci_brenda=brend.ucitaj(st.secrets))
    except Exception as e:                             # noqa: BLE001
        st.caption(f"PDF trenutno nije moguć ({e}) — koristi HTML izvještaj ispod.")
        return
    st.download_button(
        "📄 Izvještaj za roditelje (PDF)",
        data=sadrzaj,
        file_name=ime_datoteke(ucenik),
        mime="application/pdf",
        key="v2_pdf_" + (kljuc or model.tekst((ucenik or {}).get("ucenik_id")) or "x"),
    )
