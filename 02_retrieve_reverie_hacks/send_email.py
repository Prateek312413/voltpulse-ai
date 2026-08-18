"""
Reverie Hacks 2026 — Automated Email Dispatcher
Send the sponsor guides and promo codes to any recipient email using Python smtplib.

Usage:
    python send_email.py --to user@example.com --sender your_email@gmail.com --password your_app_password
Or set environment variables:
    SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAIL
"""

import argparse
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SUBJECT = "[Reverie Hacks 2026] Sponsor Access Codes & AI Setup Guides (Wolfram|One & Featherless.ai)"

HTML_BODY = """\
<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 20px; }
  .card { background: #ffffff; border-radius: 12px; padding: 24px; margin-bottom: 20px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
  h1 { color: #0f172a; margin-top: 0; }
  h2 { color: #2563eb; margin-top: 0; }
  .badge { display: inline-block; background-color: #dbeafe; color: #1e40af; padding: 4px 12px; border-radius: 9999px; font-weight: 600; font-size: 14px; margin-bottom: 12px; }
  .code-box { background: #0f172a; color: #38bdf8; padding: 14px; border-radius: 8px; font-family: monospace; font-size: 14px; overflow-x: auto; }
  a { color: #2563eb; text-decoration: none; font-weight: 600; }
  a:hover { text-decoration: underline; }
  ul { padding-left: 20px; }
  li { margin-bottom: 8px; }
</style>
</head>
<body>
  <div style="max-width: 680px; margin: 0 auto;">
    <div class="card" style="border-top: 4px solid #2563eb;">
      <h1>🚀 Reverie Hacks 2026 — Sponsor Resources</h1>
      <p>Here are your official sponsor access links, redemption codes, and API setup instructions for Reverie Hacks 2026.</p>
    </div>

    <div class="card">
      <span class="badge">COMPUTATION & ALGORITHMS</span>
      <h2>1. Wolfram|One & Wolfram API (1 Month Free)</h2>
      <ul>
        <li><strong>Redemption Link:</strong> <a href="https://account.wolfram.com/redeem/REVHACKS26">https://account.wolfram.com/redeem/REVHACKS26</a></li>
        <li><strong>Promo Code:</strong> <code>REVHACKS26</code></li>
        <li><strong>Includes:</strong> Full desktop & cloud access to Wolfram|One, Wolfram API, instant web app deployment, and cloud credits.</li>
        <li><strong>Account Details:</strong> <a href="https://account.wolfram.com/products">https://account.wolfram.com/products</a></li>
      </ul>
    </div>

    <div class="card">
      <span class="badge">SERVERLESS AI INFERENCE</span>
      <h2>2. Featherless.ai (1 Month Free Feather Premium)</h2>
      <ul>
        <li><strong>Redemption Link:</strong> <a href="https://featherless.ai">https://featherless.ai</a></li>
        <li><strong>Promo Code:</strong> <code>REVERIE26</code> ($25/mo tier, 100% OFF)</li>
        <li><strong>Includes:</strong> Unlimited serverless inference on 10,000+ open-source models (DeepSeek-V3.2, MiniMax-M2.5, Kimi-K2.5, GLM-5, Mistral-Nemo, Qwen 2.5/3, Llama 3.3).</li>
        <li><strong>Concurrency:</strong> Up to 4 concurrent connections, 32k context.</li>
        <li><strong>Model Catalog:</strong> <a href="https://featherless.ai/models">https://featherless.ai/models</a></li>
        <li><strong>Tool Integrations (Cursor, Cline, Roo Code, Aider, n8n, Dify):</strong> <a href="https://featherless.ai/docs/application-guides">Application Guides</a></li>
      </ul>
      <p><strong>Quick Python Snippet (OpenAI SDK):</strong></p>
      <pre class="code-box">from openai import OpenAI

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key="YOUR_FEATHERLESS_API_KEY"
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    messages=[{"role": "user", "content": "Hello Reverie Hacks!"}]
)
print(response.choices[0].message.content)</pre>
    </div>

    <div style="text-align: center; color: #64748b; font-size: 13px; margin-top: 24px;">
      Reverie Hacks 2026 • Happy Building! ⚡
    </div>
  </div>
</body>
</html>
"""

def send_email(to_email: str, sender_email: str, sender_password: str, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = sender_email
    msg["To"] = to_email

    msg.attach(MIMEText(HTML_BODY, "html"))

    print(f"Connecting to SMTP server {smtp_server}:{smtp_port}...")
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [to_email], msg.as_string())
    print(f"Email successfully sent to {to_email}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send Reverie Hacks sponsor perks email")
    parser.add_argument("--to", default=os.getenv("RECIPIENT_EMAIL"), help="Recipient email address")
    parser.add_argument("--sender", default=os.getenv("SENDER_EMAIL"), help="Sender email address")
    parser.add_argument("--password", default=os.getenv("SENDER_PASSWORD"), help="Sender email app password")
    parser.add_argument("--smtp", default="smtp.gmail.com", help="SMTP Server host")
    parser.add_argument("--port", type=int, default=587, help="SMTP Server port")

    args = parser.parse_args()

    if not args.to or not args.sender or not args.password:
        print("Missing credentials.")
        print("Usage: python send_email.py --to <recipient> --sender <your_email> --password <app_password>")
        print("Or set environment variables: RECIPIENT_EMAIL, SENDER_EMAIL, SENDER_PASSWORD")
    else:
        send_email(args.to, args.sender, args.password, args.smtp, args.port)
