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
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)  # black

    x = w_mm - 10
    y = h_mm / 2

    now_cet = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d %H:%M CET")
    stamp_text = (f"Document generated for {name} on {now_cet}. "
                  f"Distribution of this document without explicit authorization "
                  f"is not allowed and will be prosecuted legally by the emitting entity.")
    text_w = pdf.get_string_width(stamp_text) + 6

    with pdf.rotation(angle=90, x=x, y=y):
        pdf.set_xy(x - text_w / 2, y - 3)
        pdf.cell(text_w, 6, stamp_text, align="C")

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

