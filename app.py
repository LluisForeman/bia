from flask import Flask, render_template, request, Response, abort, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from itsdangerous import URLSafeSerializer
from scraper import scrape_all_pages
from pdf_gen import generate_pdf, generate_certificate
import hashlib, os, atexit
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bia-secret-key-change-in-prod")
_signer = URLSafeSerializer(app.secret_key, salt="cert")

VALID_NAMES: set = set()

# --- Document registry ---
# "url-slug": ("written/filename.pdf", "Display Title")
DOCUMENTS = {
    # Interview preps
    "airbus":            ("written/airbus_interview_prep.pdf",          "Airbus"),
    "arianespace":       ("written/arianespace_interview_prep.pdf",     "Arianespace"),
    "bae":               ("written/bae_interview_prep.pdf",             "BAE Systems"),
    "blueorigin":        ("written/blue_origin_interview_prep.pdf",     "Blue Origin"),
    "boeing":            ("written/boeing_interview_prep.pdf",          "Boeing"),
    "dlr":               ("written/dlr_interview_prep.pdf",             "DLR"),
    "embraer":           ("written/embraer_interview_prep.pdf",         "Embraer"),
    "esa":               ("written/esa_interview_prep.pdf",             "ESA"),
    "hanwha":            ("written/hanwha_interview_prep.pdf",          "Hanwha"),
    "jaxa":              ("written/jaxa_interview_prep.pdf",            "JAXA"),
    "khi":               ("written/khi_interview_prep.pdf",             "Kawasaki Heavy Industries"),
    "kongsberg":         ("written/kongsberg_interview_prep.pdf",       "Kongsberg"),
    "leonardo":          ("written/leonardo_interview_prep.pdf",        "Leonardo"),
    "lockheed":          ("written/lockheed_martin_interview_prep.pdf", "Lockheed Martin"),
    "nasa":              ("written/nasa_interview_prep.pdf",            "NASA"),
    "northrop":          ("written/northrop_grumman_interview_prep.pdf","Northrop Grumman"),
    "rocketlab":         ("written/rocketlab_interview_prep.pdf",       "Rocket Lab"),
    "rollsroyce":        ("written/rolls_royce_interview_prep.pdf",     "Rolls-Royce"),
    "safran":            ("written/safran_interview_prep.pdf",          "Safran"),
    "satcom-interview":  ("written/satcom_interview_prep.pdf",          "Satcom"),
    "spacex":            ("written/spacex_interview_prep.pdf",          "SpaceX"),
    "uksa":              ("written/uksa_interview_prep.pdf",            "UK Space Agency"),
    "ula":               ("written/ula_interview_prep.pdf",             "ULA"),
    # Topic guides
    "air-mobility":               ("written/air mobility.pdf",                      "Air Mobility"),
    "aircraft-leasing":           ("written/aircraft leasing.pdf",                  "Aircraft Leasing"),
    "aircraft-maintenance-europe":("written/aircraft maintenance europe.pdf",       "Aircraft Maintenance Europe"),
    "aircraft-maintenance-us":    ("written/aircraft maintenance US.pdf",           "Aircraft Maintenance US"),
    "aircraft-noise-acoustics":   ("written/aircraft noise acoustics.pdf",          "Aircraft Noise & Acoustics"),
    "aircraft-performance":       ("written/aircraft performance engineering.pdf",  "Aircraft Performance Engineering"),
    "aircraft-structures":        ("written/aircraft structures.pdf",               "Aircraft Structures"),
    "aviation-safety":            ("written/aviation safety.pdf",                   "Aviation Safety"),
    "cfd":                        ("written/cfd.pdf",                               "CFD"),
    "electric-hybrid":            ("written/electric hybrid.pdf",                   "Electric & Hybrid"),
    "electrical":                 ("written/electrical.pdf",                        "Electrical Systems"),
    "eo":                         ("written/eo.pdf",                                "Earth Observation"),
    "gnss":                       ("written/gnss.pdf",                              "GNSS"),
    "in-space":                   ("written/in space.pdf",                          "In-Space"),
    "load-control":               ("written/load control.pdf",                      "Load Control"),
    "market-intelligence":        ("written/market intelligence.pdf",               "Market Intelligence"),
    "rocket-propulsion":          ("written/rocket propulsion engineering.pdf",     "Rocket Propulsion Engineering"),
    "satcom":                     ("written/satcom.pdf",                            "Satcom"),
}

# --- Certificate registry ---
# "cert-slug": "Course Title"
CERTIFICATES = {
    "aircraft-intro":        "Aerospace Engineering: Aircraft Introduction",
    "aircraft-fundamentals": "Aerospace Engineering: Aircraft Fundamentals",
    "aircraft-systems":      "Aerospace Engineering: Aircraft Systems and Avionics",
    "aircraft-structures":   "Aerospace Engineering: Aircraft Structures and Materials",
    "airlines-airports":     "Aerospace Engineering: Airlines, Aircraft and Airports",
    "aircraft-avionics":     "Aerospace Engineering: Aircraft Avionics and Cockpit",
    "aircraft-aerodynamics": "Aerospace Engineering: Aircraft Aerodynamics",
    "aircraft-design":       "Aerospace Engineering: Aircraft Optimal Design and Performance",
    "aircraft-jet-engines":  "Aerospace Engineering: Aircraft Jet Engines",
    "airlines-management":   "Airlines Management: Operations and Business Models",
    "aircraft-electrical":   "Aerospace Engineering: Aircraft Electrical Systems",
    "10-aircraft":           "Aerospace Engineering: 10 Aircraft Explained",
    "astronautics":          "Astronautics and SpaceTech for Future Human Missions",
    "spacecraft-engineering":"Interplanetary Spacecraft and Satellite Engineering",
    "rocket-fundamentals":   "Aerospace Engineering: Rocket Fundamentals",
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


# ── Interview doc routes ──────────────────────────────────────────────────────

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


# ── Certificate routes ────────────────────────────────────────────────────────

@app.route("/cert/<course_slug>")
def cert_page(course_slug):
    if course_slug not in CERTIFICATES:
        abort(404)
    course_title = CERTIFICATES[course_slug]
    return render_template("cert.html", error=None, warming=False,
                           course_slug=course_slug, course_title=course_title)


@app.route("/cert/<course_slug>/verify", methods=["POST"])
def cert_verify(course_slug):
    if course_slug not in CERTIFICATES:
        abort(404)

    course_title = CERTIFICATES[course_slug]
    name = request.form.get("name", "").strip()
    print(f"[cert] course={course_slug} submitted='{name}' loaded={len(VALID_NAMES)}")

    if not VALID_NAMES:
        return render_template("cert.html", warming=True, error=None,
                               course_slug=course_slug, course_title=course_title)

    if name not in VALID_NAMES:
        return render_template("cert.html",
                               error="Name not recognised. Check spelling and capitalisation exactly as it appears in the community.",
                               warming=False, course_slug=course_slug, course_title=course_title)

    # Generate deterministic cert ID from name + course
    raw = f"{app.secret_key}:{name}:{course_slug}"
    cert_id = "cert_" + hashlib.sha256(raw.encode()).hexdigest()[:8]

    # Issue date in CET
    issued = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%A, %B %-d, %Y")

    # Sign a token encoding all the data needed to regenerate the PDF
    token = _signer.dumps({"name": name, "course": course_slug, "cert_id": cert_id, "issued": issued})

    return redirect(url_for("cert_view", course_slug=course_slug, token=token))


@app.route("/cert/<course_slug>/view/<token>")
def cert_view(course_slug, token):
    if course_slug not in CERTIFICATES:
        abort(404)
    try:
        data = _signer.loads(token)
    except Exception:
        abort(400)

    name        = data["name"]
    cert_id     = data["cert_id"]
    issued      = data["issued"]
    course_title = CERTIFICATES[course_slug]

    pdf_bytes = generate_certificate(name, course_title, cert_id, issued)
    filename = f"certificate_{name.replace(' ', '_')}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )


# ── Utility routes ────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return "ok", 200


@app.route("/debug")
def debug():
    sample = sorted(list(VALID_NAMES))[:10]
    return {"count": len(VALID_NAMES), "sample": sample}, 200


if __name__ == "__main__":
    app.run(debug=True)
