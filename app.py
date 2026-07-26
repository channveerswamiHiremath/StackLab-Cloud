from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
import os
from datetime import datetime
from email.message import EmailMessage
from email.utils import formatdate
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)  # allows the HTML page to POST to this backend from any domain

# ── credentials ── load from environment or paste directly for testing
YOUR_EMAIL = os.getenv("EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
NOTIFY_TO    = YOUR_EMAIL   # where YOU receive the access-request notifications

# ── logo (embedded inline in the emails below) ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "favicon.png")
LOGO_CID = "stacklab_logo"


def _attach_logo(msg):
    """Embed the StackLab Cloud logo as an inline image (cid) on the HTML part."""
    if os.path.exists(LOGO_PATH):
        html_part = msg.get_payload()[-1]
        with open(LOGO_PATH, "rb") as f:
            html_part.add_related(f.read(), maintype="image", subtype="png", cid=f"<{LOGO_CID}>")
    else:
        print(f"[warning] logo not found at {LOGO_PATH} — email will send without it")


def _email_shell(inner_html):
    """Shared AWS-style wrapper: dark header with logo, blue accent bar, white card, footer."""
    year = datetime.utcnow().year
    return f"""\
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f0efe8;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0efe8;padding:32px 0;">
  <tr>
    <td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:92%;background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 10px rgba(13,13,11,0.06);">

        <!-- Header -->
        <tr>
          <td style="background-color:#0d0d0b;padding:28px 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td valign="middle" width="40">
                  <img src="cid:{LOGO_CID}" alt="StackLab Cloud" width="40" height="40" style="display:block;border-radius:6px;">
                </td>
                <td valign="middle" style="padding-left:12px;">
                  <span style="font-size:18px;font-weight:700;color:#ffffff;letter-spacing:-0.02em;">StackLab&nbsp;<span style="color:#4f9cff;">Cloud</span></span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Accent bar -->
        <tr><td style="height:4px;background:linear-gradient(90deg,#2563eb,#4f9cff);font-size:0;line-height:0;">&nbsp;</td></tr>

        <!-- Body -->
        {inner_html}

        <!-- Footer -->
        <tr>
          <td style="background-color:#faf9f6;border-top:1px solid #e2e1da;padding:22px 36px;">
            <p style="margin:0;font-size:12px;color:#8f8f86;line-height:1.6;">
              This is an automated message from StackLab Cloud.
            </p>
            <p style="margin:8px 0 0 0;font-size:12px;color:#b0b0a8;">© {year} StackLab Cloud</p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>
"""


def build_notification_html(name, email, access, purpose):
    purpose_html = purpose if purpose else "<span style=\"color:#8a8a86;\">Not provided</span>"
    timestamp = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
    inner = f"""\
        <tr>
          <td style="padding:36px 36px 8px 36px;">
            <span style="display:inline-block;background:#eff4ff;color:#2563eb;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:5px 12px;border-radius:20px;">New Access Request</span>
            <h1 style="margin:18px 0 6px 0;font-size:22px;color:#0d0d0b;letter-spacing:-0.02em;">A new access request just came in</h1>
            <p style="margin:0 0 24px 0;font-size:14px;line-height:1.7;color:#505048;">
              Someone submitted the &ldquo;Get Access&rdquo; form on StackLab Cloud. Details are below.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e1da;border-radius:6px;overflow:hidden;">
              <tr>
                <td style="padding:14px 18px;background-color:#faf9f6;border-bottom:1px solid #e2e1da;width:34%;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#8f8f86;">Name</td>
                <td style="padding:14px 18px;background-color:#faf9f6;border-bottom:1px solid #e2e1da;font-size:14px;color:#0d0d0b;">{name}</td>
              </tr>
              <tr>
                <td style="padding:14px 18px;border-bottom:1px solid #e2e1da;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#8f8f86;">Email</td>
                <td style="padding:14px 18px;border-bottom:1px solid #e2e1da;font-size:14px;"><a href="mailto:{email}" style="color:#2563eb;text-decoration:none;">{email}</a></td>
              </tr>
              <tr>
                <td style="padding:14px 18px;background-color:#faf9f6;border-bottom:1px solid #e2e1da;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#8f8f86;">Requested access</td>
                <td style="padding:14px 18px;background-color:#faf9f6;border-bottom:1px solid #e2e1da;font-size:14px;color:#0d0d0b;">{access}</td>
              </tr>
              <tr>
                <td style="padding:14px 18px;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#8f8f86;vertical-align:top;">Use case</td>
                <td style="padding:14px 18px;font-size:14px;color:#0d0d0b;line-height:1.6;">{purpose_html}</td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 36px 8px 36px;">
            <a href="mailto:{email}" style="display:inline-block;background-color:#2563eb;color:#ffffff;text-decoration:none;font-size:14px;font-weight:600;padding:12px 26px;border-radius:4px;">Reply to {name.split(' ')[0] if name else 'requester'} →</a>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 36px 0 36px;">
            <p style="margin:0;font-size:12px;color:#8f8f86;">Submitted {timestamp}</p>
          </td>
        </tr>
"""
    return _email_shell(inner)


def build_confirmation_html(name, access):
    inner = f"""\
        <tr>
          <td style="padding:36px 36px 8px 36px;">
            <span style="display:inline-block;background:#eff4ff;color:#2563eb;font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;padding:5px 12px;border-radius:20px;">Request Received</span>
            <h1 style="margin:18px 0 6px 0;font-size:22px;color:#0d0d0b;letter-spacing:-0.02em;">Thanks for requesting access, {name.split(' ')[0] if name else name}!</h1>
            <p style="margin:0 0 24px 0;font-size:14px;line-height:1.7;color:#505048;">
              We've received your request to join StackLab Cloud. Our team reviews every request
              personally, and you'll receive your login credentials within <strong>24 hours</strong>.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 36px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e1da;border-radius:6px;overflow:hidden;">
              <tr>
                <td style="padding:14px 18px;background-color:#faf9f6;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#8f8f86;width:34%;">Requested access</td>
                <td style="padding:14px 18px;background-color:#faf9f6;font-size:14px;color:#0d0d0b;">{access}</td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:28px 36px 0 36px;">
            <p style="margin:0;font-size:14px;line-height:1.7;color:#505048;">
              — The StackLab Team
            </p>
          </td>
        </tr>
"""
    return _email_shell(inner)


def send_notification(name, email, access, purpose):
    """Send yourself an email when someone submits the form."""
    msg = EmailMessage()
    msg["Subject"] = f"[StackLab] Access request from {name}"
    msg["From"]    = YOUR_EMAIL
    msg["To"]      = NOTIFY_TO
    msg["Date"]    = formatdate(localtime=True)

    body = f"""New access request received on StackLab Cloud.

Name    : {name}
Email   : {email}
Access  : {access}
Purpose : {purpose or "Not provided"}

---
Reply to this email or contact them directly at {email}.
"""
    msg.set_content(body)
    msg.add_alternative(build_notification_html(name, email, access, purpose), subtype="html")
    _attach_logo(msg)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(YOUR_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)


def send_confirmation(name, email, access):
    """Send the user a confirmation that their request was received."""
    msg = EmailMessage()
    msg["Subject"] = "Your StackLab Cloud access request"
    msg["From"]    = YOUR_EMAIL
    msg["To"]      = email
    msg["Date"]    = formatdate(localtime=True)

    body = f"""Hi {name},

Thanks for requesting access to StackLab Cloud!

We've received your request for: {access}

We'll review it and send your login credentials within 24 hours.

— The StackLab Team
"""
    msg.set_content(body)
    msg.add_alternative(build_confirmation_html(name, access), subtype="html")
    _attach_logo(msg)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(YOUR_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)


@app.route("/request-access", methods=["POST"])
def request_access():
    data    = request.get_json(force=True)
    name    = data.get("name", "").strip()
    email   = data.get("email", "").strip()
    access  = data.get("access", "Not specified")
    purpose = data.get("purpose", "")

    if not name or not email:
        return jsonify({"ok": False, "error": "Name and email are required"}), 400

    try:
        send_notification(name, email, access, purpose)
        send_confirmation(name, email, access)
        return jsonify({"ok": True})
    except Exception as e:
        print(f"SMTP error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Run with:  python app.py
    # Or in production:  gunicorn app:app
    app.run(debug=True, port=5000)