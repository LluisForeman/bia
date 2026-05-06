import io
from datetime import datetime
from zoneinfo import ZoneInfo
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter


def _make_name_stamp(name: str, width_pt: float, height_pt: float) -> bytes:
    """
    Create a single-page PDF (same size as the source page) containing only
    the member's name printed vertically on the right side.
    """
    w_mm = width_pt * 25.4 / 72
    h_mm = height_pt * 25.4 / 72

    pdf = FPDF(unit="mm", format=(w_mm, h_mm))
    pdf.add_page()

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)

    now_cet = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M CET")
    line1 = f"Document generated for {name} on {now_cet}."
    line2 = ("Distribution of this document without explicit authorization "
             "is not allowed and will be prosecuted legally by the emitting entity.")

    y = h_mm / 2
    for x_pos, text in [(w_mm - 7, line1), (w_mm - 13, line2)]:
        text_w = pdf.get_string_width(text) + 6
        with pdf.rotation(angle=90, x=x_pos, y=y):
            pdf.set_xy(x_pos - text_w / 2, y - 3)
            pdf.cell(text_w, 6, text, align="C")

    return bytes(pdf.output())


def generate_pdf(name: str, pdf_path: str) -> bytes:
    """
    Read the PDF at pdf_path, stamp the member's name vertically on the
    right side of every page, and return the result as bytes.
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        width_pt  = float(page.mediabox.width)
        height_pt = float(page.mediabox.height)

        stamp_bytes = _make_name_stamp(name, width_pt, height_pt)
        stamp_page  = PdfReader(io.BytesIO(stamp_bytes)).pages[0]

        page.merge_page(stamp_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


# ── Certificate generation ────────────────────────────────────────────────────

CERT_TEMPLATE = "certificate_valueknow.pdf"
FONT_PATH     = "DancingScript.ttf"

# Template: 720 x 540 pt = 254 x 190.5 mm, landscape
_W_MM = 254.0
_H_MM = 190.5


def generate_certificate(name: str, course_title: str, cert_id: str, issued: str) -> bytes:
    """
    Overlay name (Dancing Script), course title, date and cert ID
    onto the ValueKnow certificate template and return PDF bytes.
    """
    # Do NOT pass orientation="L" — the format tuple already defines landscape
    # (254 > 190.5). Passing orientation would swap the dimensions and break alignment.
    overlay = FPDF(unit="mm", format=(_W_MM, _H_MM))
    overlay.set_auto_page_break(False)   # prevent accidental page breaks
    overlay.add_page()

    # Member name — Dancing Script, baseline lands ~64mm from top; move up to ~58mm
    overlay.add_font("DancingScript", "", FONT_PATH)
    overlay.set_font("DancingScript", "", 36)
    overlay.set_text_color(20, 20, 20)
    overlay.set_xy(18, 61)
    overlay.cell(160, 14, name, align="L")

    # Course title — force split at ':' to match template layout
    overlay.set_font("Helvetica", "B", 18)
    overlay.set_text_color(20, 20, 20)
    if ":" in course_title:
        part1, part2 = course_title.split(":", 1)
        overlay.set_xy(14, 97)
        overlay.cell(170, 10, part1 + ":", align="L")
        overlay.set_xy(14, 108)
        overlay.cell(170, 10, part2.strip(), align="L")
    else:
        overlay.set_xy(14, 97)
        overlay.multi_cell(155, 10, course_title, align="L")

    # Date — baseline must land BELOW instructor (at 168mm); set y=172
    overlay.set_font("Helvetica", "", 9)
    overlay.set_text_color(60, 60, 60)
    overlay.set_xy(18, 172)
    overlay.cell(90, 5, issued, align="L")

    # Certificate ID — centred across full page width
    overlay.set_xy(0, 172)
    overlay.cell(_W_MM, 5, f"Certificate ID: {cert_id}", align="C")

    overlay_bytes = bytes(overlay.output())

    # Merge overlay onto template
    reader   = PdfReader(CERT_TEMPLATE)
    template = reader.pages[0]
    stamp    = PdfReader(io.BytesIO(overlay_bytes)).pages[0]
    template.merge_page(stamp)

    writer = PdfWriter()
    writer.add_page(template)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
