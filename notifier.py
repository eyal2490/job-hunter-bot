"""
Telegram bot notifier.

Sends a message per matching job, using the bot token and chat ID
provided via environment variables (configured as GitHub Secrets).
"""

import os
import requests
import html

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


def _escape(text):
    """Escape characters that have special meaning in Telegram HTML mode."""
    if text is None:
        return ""
    return html.escape(str(text))


def send_job(job):
    """Send a single job posting to Telegram."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("[telegram] missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return False

    title = _escape(job.get("title", "(no title)"))
    company = _escape(job.get("company", ""))
    location = _escape(job.get("location", ""))
    url = job.get("url", "")

    text = (
        f"🔔 <b>{title}</b>\n"
        f"🏢 {company}\n"
    )
    if location:
        text += f"📍 {location}\n"
    if url:
        text += f"\n<a href=\"{_escape(url)}\">צפה במשרה</a>"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        r = requests.post(TELEGRAM_API_BASE.format(token=token), json=payload, timeout=15)
        if r.status_code != 200:
            print(f"[telegram] error {r.status_code}: {r.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"[telegram] exception: {e}")
        return False


def send_status(text):
    """Send a plain status message (used for run summaries / error reports)."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return False

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(TELEGRAM_API_BASE.format(token=token), json=payload, timeout=15)
        return r.status_code == 200
    except Exception:
        return False
