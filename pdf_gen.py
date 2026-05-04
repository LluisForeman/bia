import io
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

SOURCE_PDF = "written/DLR.pdf"


def _make_name_stamp(name: str, width_pt: float, height_pt: float) -> bytes:
    """
    Create a single-page PDF (same size as the source page) containing only
    the member's name printed vertically on the right side.
    """
    # fpdf2 works in mm; convert from PDF points (1 pt = 25.4/72 mm)
    w_mm = width_pt * 25.4 / 72
    h_mm = height_pt * 25.4 / 72

    pdf = FPDF(unit="mm", format=(w_mm, h_mm))
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(180, 50, 50)   # subtle red — visible but not intrusive

    # Right edge: 10 mm from right, vertically centred
    x = w_mm - 10
    y = h_mm / 2

    text_w = pdf.get_string_width(name) + 6

    # Rotate 90° so text reads bottom-to-top along the right margin
    with pdf.rotation(angle=90, x=x, y=y):
        pdf.set_xy(x - text_w / 2, y - 3)
        pdf.cell(text_w, 6, name, align="C")

    return bytes(pdf.output())


def generate_pdf(name: str) -> bytes:
    """
    Read source.pdf, stamp the member's name vertically on the right side
    of every page, and return the resulting PDF as bytes.
    """
    reader = PdfReader(SOURCE_PDF)
    writer = PdfWriter()

    for page in reader.pages:
        width_pt  = float(page.mediabox.width)
        height_pt = float(page.mediabox.height)

        # Build a stamp page the same size as this page
        stamp_bytes = _make_name_stamp(name, width_pt, height_pt)
        stamp_page  = PdfReader(io.BytesIO(stamp_bytes)).pages[0]

        # Overlay the stamp on top of the original page
        page.merge_page(stamp_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
