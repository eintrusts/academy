"""PDF certificate generation (fpdf2)."""
import io
import urllib.request
from datetime import datetime
from functools import lru_cache

from fpdf import FPDF

from . import config

GREEN = (46, 125, 50)
DARK = (33, 33, 33)
GREY = (110, 110, 110)


def _latin1(text):
    # The core PDF fonts are Latin-1 only; replace anything else rather than failing.
    return str(text or "").encode("latin-1", "replace").decode("latin-1")


@lru_cache(maxsize=1)
def _logo_bytes():
    try:
        with urllib.request.urlopen(config.LOGO_URL, timeout=5) as resp:
            return resp.read()
    except Exception:  # offline or URL moved - certificates fall back to text branding
        return None


def verification_hint(cert_id):
    base = config.app_url()
    if base:
        return f"Verify at {base}/verify?id={cert_id}"
    return f"Verify this certificate on the {config.BRAND_NAME} website using ID {cert_id}"


def build_certificate(full_name, course_title, cert_id, issued_at, duration_hours=None):
    """Return the certificate as PDF bytes."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    w, h = pdf.w, pdf.h

    # Borders
    pdf.set_draw_color(*GREEN)
    pdf.set_line_width(2.5)
    pdf.rect(8, 8, w - 16, h - 16)
    pdf.set_line_width(0.6)
    pdf.rect(13, 13, w - 26, h - 26)

    top = 32
    logo = _logo_bytes()
    if logo:
        try:
            pdf.image(io.BytesIO(logo), x=w / 2 - 12, y=20, w=24)
            top = 50
        except Exception:  # unreadable image - text branding is enough
            pass

    pdf.set_text_color(*GREEN)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(0, top)
    pdf.cell(w, 8, _latin1(config.BRAND_NAME.upper()), align="C")

    pdf.set_text_color(*DARK)
    pdf.set_font("Helvetica", "B", 34)
    pdf.set_xy(0, top + 14)
    pdf.cell(w, 16, "Certificate of Completion", align="C")

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*GREY)
    pdf.set_xy(0, top + 38)
    pdf.cell(w, 8, "This is to certify that", align="C")

    pdf.set_text_color(*DARK)
    pdf.set_font("Times", "BI", 30)
    pdf.set_xy(0, top + 50)
    pdf.cell(w, 14, _latin1(full_name), align="C")
    pdf.set_draw_color(*GREY)
    pdf.set_line_width(0.3)
    pdf.line(w / 2 - 70, top + 66, w / 2 + 70, top + 66)

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(*GREY)
    pdf.set_xy(0, top + 72)
    pdf.cell(w, 8, "has successfully completed the course", align="C")

    pdf.set_text_color(*GREEN)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(30, top + 84)
    pdf.multi_cell(w - 60, 10, _latin1(course_title), align="C")

    issued = issued_at
    try:
        issued = datetime.strptime(issued_at, "%Y-%m-%d %H:%M:%S").strftime("%d %B %Y")
    except (TypeError, ValueError):
        pass
    details = f"Issued on {issued}"
    if duration_hours:
        details += f"  |  {duration_hours:g} learning hours"

    pdf.set_text_color(*DARK)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(25, h - 42)
    pdf.cell(100, 6, _latin1(details))
    pdf.set_xy(25, h - 35)
    pdf.cell(100, 6, _latin1(f"Certificate ID: {cert_id}"))

    pdf.set_xy(w - 125, h - 42)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(100, 6, _latin1(config.COMPANY_NAME), align="R")
    pdf.set_xy(w - 125, h - 35)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(100, 6, _latin1(config.COMPANY_WEBSITE.replace("https://", "")), align="R")

    pdf.set_text_color(*GREY)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_xy(0, h - 24)
    pdf.cell(w, 5, _latin1(verification_hint(cert_id)), align="C")

    return bytes(pdf.output())
