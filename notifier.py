"""
Telegram bot notifier.
"""

import os
import requests
import html

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


def _escape(text):
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
    posted = _escape(job.get("posted_on", ""))
    url = job.get("url", "")

    # If the job says "Posted Today" or similar, flag it as hot.
    # Workday strings: "Posted Today", "Posted Yesterday", "Posted X Days Ago"
    posted_lower = (job.get("posted_on", "") or "").lower()
    is_hot = "today" in posted_lower or "just posted" in posted_lower

    if is_hot:
        text = f"🔥 <b>BRAND NEW JOB - APPLY NOW!</b>\n\n"
        text += f"<b>{title}</b>\n"
    else:
        text = f"🔔 <b>{title}</b>\n"

    text += f"🏢 {company}\n"
    if location:
        text += f"📍 {location}\n"
    if posted:
        text += f"🕒 {posted}\n"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    if url:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "🔗 Apply Now", "url": url}
            ]]
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
