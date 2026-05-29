"""
NexusFlow Agent — Email Notifications (Phase 4)
Sends real emails via Gmail SMTP when the agent needs human attention.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_agent_notification(subject: str, body: str, to_email: str = None) -> bool:
    """
    Send an email notification from the agent to the human reviewer.
    
    Args:
        subject: Email subject line
        body: Plain text email body
        to_email: Recipient (defaults to your own Gmail)
    
    Returns:
        True if sent successfully, False if failed
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("[EMAIL] Gmail not configured — skipping notification")
        return False

    recipient = to_email or GMAIL_ADDRESS

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, recipient, msg.as_string())
        print(f"[EMAIL] ✅ Sent: {subject}")
        return True
    except Exception as e:
        print(f"[EMAIL] ❌ Failed: {e}")
        return False


def send_cycle_report(report: dict) -> bool:
    """
    Send a summary email after each agent cycle.
    Only sends if there are flags or actions that need attention.
    """
    actions = report.get("actions_taken", [])
    summary = report.get("summary", "")
    cycle_id = report.get("cycle_id", "unknown")

    # Count flags
    flags = [a for a in actions if a["tool"] == "flag_for_human_review"]

    if not flags:
        print("[EMAIL] No flags this cycle — skipping notification email")
        return False

    subject = f"[NexusFlow Agent] {len(flags)} item(s) need your attention — {cycle_id}"

    body = f"""NexusFlow Autonomous CRM Agent — Cycle Report
{'='*50}
Cycle ID: {cycle_id}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'='*50}

ITEMS REQUIRING HUMAN REVIEW:
"""
    for flag in flags:
        try:
            import json
            result = json.loads(flag["result"])
            flag_data = result.get("flag", {})
            body += f"""
- [{flag_data.get('priority', 'UNKNOWN')}] {flag_data.get('customer_name', 'Unknown')}
  Reason: {flag_data.get('reason', '')}
  Details: {flag_data.get('details', '')}
"""
        except Exception:
            body += f"\n• {flag['tool']} — see logs for details\n"

    body += f"""
{'='*50}
FULL CYCLE SUMMARY:
{summary}

{'='*50}
Actions taken this cycle: {len(actions)}
Report saved to: logs/agent_actions.jsonl

— NexusFlow Agent
"""

    return send_agent_notification(subject, body)