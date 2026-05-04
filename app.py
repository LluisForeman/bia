from flask import Flask, render_template, request, Response, abort
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import scrape_all_pages
from pdf_gen import generate_pdf
import atexit

app = Flask(__name__)
VALID_NAMES: set = set()

# --- Document registry ---
# Add your files here: "url-slug": ("written/filename.pdf", "Display Title")
DOCUMENTS = {
    "dlr":         ("written/DLR.pdf",     "DLR"),
    "spacex":      ("written/SpaceX.pdf",  "SpaceX"),
    "esa":         ("written/ESA.pdf",     "ESA"),
    "nasa":        ("written/NASA.pdf",    "NASA"),
    "airbus":      ("written/Airbus.pdf",  "Airbus"),
    "boeing":      ("written/Boeing.pdf",  "Boeing"),
    "lockheed":    ("written/Lockheed.pdf","Lockheed Martin"),
    "northrop":    ("written/Northrop.pdf","Northrop Grumman"),
    "raytheon":    ("written/Raytheon.pdf","Raytheon"),
    "blueorigin":  ("written/BlueOrigin.pdf", "Blue Origin"),
}

def refresh_names():
    global VALID_NAMES
    VALID_NAMES = scrape_all_pages()

# Load names synchronously — gunicorn binds the port before this runs
refresh_names()

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_names, "interval", hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


@app.route("/")
def index():
    return render_template("index.html", error=None, warming=False,
                           slug=None, title="your")


@app.route("/<slug>")
def doc_page(slug):
    if slug not in DOCUMENTS:
        abort(404)
    _, title = DOCUMENTS[slug]
    return render_template("index.html", error=None, warming=False, slug=slug, title=title)


@app.route("/<slug>/verify", methods=["POST"])
def verify(slug):
    if slug not in DOCUMENTS:
        abort(404)

    pdf_path, title = DOCUMENTS[slug]
    name = request.form.get("name", "").strip()
    print(f"[verify] slug={slug} submitted='{name}' loaded={len(VALID_NAMES)}")

    if not VALID_NAMES:
        return render_template("index.html", warming=True, error=None, slug=slug, title=title)

    if name not in VALID_NAMES:
        return render_template("index.html",
                               error="Name not recognised. Check spelling and capitalisation exactly as it appears in the community.",
                               warming=False, slug=slug, title=title)

    pdf_bytes = generate_pdf(name, pdf_path)
    filename = f"{slug}_{name.replace(' ', '_')}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/health")
def health():
    return "ok", 200


@app.route("/debug")
def debug():
    sample = sorted(list(VALID_NAMES))[:10]
    return {"count": len(VALID_NAMES), "sample": sample}, 200


if __name__ == "__main__":
    app.run(debug=True)
