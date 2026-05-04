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
    # Two vertical strips side by side — rightmost first
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

