from fpdf import FPDF

def generate_pdf(name: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_fill_color(60, 80, 180)
    pdf.rect(0, 0, 210, 20, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_y(6)
    pdf.cell(0, 8, "BREAK INTO AEROSPACE", align="C")

    pdf.set_text_color(30, 30, 60)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_y(35)
    pdf.cell(0, 10, "Member Resource Document", align="C", ln=True)

    pdf.set_draw_color(180, 190, 220)
    pdf.set_line_width(0.3)
    pdf.line(20, 50, 190, 50)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 100)
    pdf.set_y(60)
    body = [
        "This document has been generated exclusively for the member identified below.",
        "It contains proprietary content belonging to the Break Into Aerospace community.",
        "",
        "Please read all sections carefully. This material is intended solely for your",
        "personal use as a registered member. Sharing, reproducing, or distributing",
        "this document in any form without prior written authorization from the issuing",
        "entity is strictly prohibited and may result in legal action.",
    ]
    for line in body:
        pdf.cell(0, 7, line, align="C", ln=True)

    pdf.set_fill_color(240, 243, 255)
    pdf.set_draw_color(60, 80, 180)
    pdf.set_line_width(0.4)
    pdf.rect(20, 240, 170, 32, 'FD')

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(60, 80, 180)
    pdf.set_xy(25, 245)
    pdf.cell(0, 5, "DOCUMENT SIGNATURE", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 80)
    pdf.set_x(25)
    pdf.cell(0, 5, f"Document generated for {name}.", ln=True)
    pdf.set_x(25)
    pdf.cell(0, 5, "Distribution of this document without explicit authorization can and will be", ln=True)
    pdf.set_x(25)
    pdf.cell(0, 5, "prosecuted legally by the emitting entity.", ln=True)

    return bytes(pdf.output())
