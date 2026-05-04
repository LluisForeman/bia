from flask import Flask, render_template, request, Response
from apscheduler.schedulers.background import BackgroundScheduler
from scraper import scrape_all_pages
from pdf_gen import generate_pdf
import threading
import atexit

app = Flask(__name__)
VALID_NAMES: set = set()

def refresh_names():
    global VALID_NAMES
    VALID_NAMES = scrape_all_pages()

# Run initial scrape in background so gunicorn can bind to port immediately
threading.Thread(target=refresh_names, daemon=True).start()

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_names, "interval", hours=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route("/")
def index():
    return render_template("index.html", error=None)

@app.route("/verify", methods=["POST"])
def verify():
    name = request.form.get("name", "").strip()
    print(f"[verify] submitted: '{name}' | total names loaded: {len(VALID_NAMES)}")
    # Show closest names to help debug
    close = [n for n in VALID_NAMES if name.lower() in n.lower() or n.lower() in name.lower()]
    print(f"[verify] partial matches: {close[:5]}")
    if name not in VALID_NAMES:
        return render_template("index.html", error="Name not recognised. Check spelling and capitalisation exactly as it appears in the community.")
    pdf_bytes = generate_pdf(name)
    filename = f"document_{name.replace(' ', '_')}.pdf"
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
