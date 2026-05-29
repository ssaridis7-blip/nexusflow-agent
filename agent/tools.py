"""
NexusFlow Agent — Tools (Phase 2)
Now connected to the real FastAPI CRM instead of stubs.
"""

import json
import requests
from datetime import datetime, date
from langchain_core.tools import tool

CRM_BASE = "http://localhost:8000"


def _get(endpoint: str, params: dict = None) -> dict:
    """Helper to call the CRM API."""
    try:
        r = requests.get(f"{CRM_BASE}{endpoint}", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "CRM API is not running. Start it with: python crm/api.py"}
    except Exception as e:
        return {"error": str(e)}


def _days_since(date_str: str) -> int:
    """Calculate how many days since a given date string (YYYY-MM-DD)."""
    if not date_str:
        return 0
    try:
        past = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (date.today() - past).days
    except:
        return 0


# ─────────────────────────────────────────────
# MONITORING TOOLS
# ─────────────────────────────────────────────

@tool
def get_overdue_invoices() -> str:
    """
    Fetch all overdue invoices from the NexusFlow CRM.
    Returns invoices where status is 'Overdue'.
    """
    data = _get("/api/invoices", {"status": "Overdue"})

    if "error" in data:
        return json.dumps(data)

    invoices = data.get("invoices", [])

    # Enrich with days overdue
    enriched = []
    for inv in invoices:
        days_overdue = _days_since(inv.get("due_date"))
        enriched.append({
            "invoice_id": inv["id"],
            "contact_id": inv["contact_id"],
            "company": inv["company"],
            "amount_gbp": inv["amount"],
            "due_date": inv["due_date"],
            "days_overdue": days_overdue,
            "description": inv["description"],
            "status": inv["status"]
        })

    return json.dumps({
        "overdue_invoices": enriched,
        "count": len(enriched),
        "total_overdue_gbp": sum(i["amount_gbp"] for i in enriched),
        "retrieved_at": datetime.now().isoformat()
    }, indent=2)


@tool
def get_stale_deals() -> str:
    """
    Fetch deals with no activity in 14 or more days.
    Checks last_contact_date on the associated contact.
    """
    data = _get("/api/deals")

    if "error" in data:
        return json.dumps(data)

    deals = data.get("deals", [])
    stale = []

    for deal in deals:
        # Skip lost deals
        if deal.get("stage") == "Lost":
            continue

        # Get the contact to check last contact date
        contact_data = _get(f"/api/contacts/{deal['contact_id']}")
        if "error" in contact_data:
            continue

        contact = contact_data.get("contact", {})
        last_contact = contact.get("last_contact_date")
        days_stale = _days_since(last_contact)

        if days_stale >= 14:
            stale.append({
                "deal_id": deal["id"],
                "deal_name": deal["deal_name"],
                "contact_id": deal["contact_id"],
                "company": deal["company"],
                "customer_name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                "deal_value_gbp": deal["value"],
                "stage": deal["stage"],
                "probability": deal["probability"],
                "last_contact": last_contact,
                "days_stale": days_stale,
                "sales_rep": deal["rep"]
            })

    return json.dumps({
        "stale_deals": stale,
        "count": len(stale),
        "retrieved_at": datetime.now().isoformat()
    }, indent=2)


@tool
def get_unengaged_leads() -> str:
    """
    Fetch churned customers and leads with no follow-up within required timeframes.
    Churned = no contact in 30+ days. Leads = no contact in 7+ days.
    """
    contacts_data = _get("/api/contacts")

    if "error" in contacts_data:
        return json.dumps(contacts_data)

    contacts = contacts_data.get("contacts", [])
    uncontacted_leads = []
    churned_no_reengagement = []

    for c in contacts:
        days = _days_since(c.get("last_contact_date"))
        name = f"{c['first_name']} {c['last_name']}"
        status = c.get("lead_status", "")

        if status == "Churned" and days >= 30:
            churned_no_reengagement.append({
                "customer_id": c["id"],
                "customer_name": name,
                "company": c["company"],
                "status": status,
                "email": c["email"],
                "last_contact": c.get("last_contact_date"),
                "days_since_contact": days,
                "notes": c.get("notes", ""),
                "sales_rep": c.get("assigned_rep")
            })

        elif status in ["New Lead", "Qualified Lead"] and days >= 7:
            uncontacted_leads.append({
                "customer_id": c["id"],
                "customer_name": name,
                "company": c["company"],
                "status": status,
                "email": c["email"],
                "last_contact": c.get("last_contact_date"),
                "days_since_contact": days,
                "notes": c.get("notes", ""),
                "sales_rep": c.get("assigned_rep")
            })

    return json.dumps({
        "uncontacted_leads": uncontacted_leads,
        "churned_no_reengagement": churned_no_reengagement,
        "count": len(uncontacted_leads) + len(churned_no_reengagement),
        "retrieved_at": datetime.now().isoformat()
    }, indent=2)


# ─────────────────────────────────────────────
# ACTION TOOLS
# ─────────────────────────────────────────────

@tool
def draft_followup_email(customer_name: str, customer_id: str, reason: str, context: str) -> str:
    """
    Draft a personalised follow-up email for a customer.

    Args:
        customer_name: Full name of the contact
        customer_id: CRM customer ID (e.g. C003)
        reason: Why we are following up (overdue_invoice / stale_deal / lead_nurture / churn_reengagement)
        context: Additional context to personalise the email
    """
    templates = {
        "overdue_invoice": f"""Subject: Friendly reminder — Outstanding invoice for {customer_name}

Dear {customer_name},

I hope this message finds you well. I'm reaching out as our records show an invoice remains outstanding on your account.

{context}

I'd appreciate it if you could confirm receipt and let us know when we can expect payment. If there's anything we can help resolve, please don't hesitate to get in touch.

Warm regards,
NexusFlow Solutions Accounts Team""",

        "stale_deal": f"""Subject: Following up — {customer_name} x NexusFlow

Dear {customer_name},

I wanted to check in following our recent conversations about NexusFlow. I want to make sure you have everything you need to move forward.

{context}

Would you be available for a 20-minute call this week? I'm happy to answer any outstanding questions or walk through the proposal again.

Best regards,
NexusFlow Sales Team""",

        "lead_nurture": f"""Subject: Still here to help — NexusFlow Solutions

Dear {customer_name},

Thank you for your interest in NexusFlow. I wanted to follow up and see if you'd had a chance to review the information we sent over.

{context}

Our team would love to set up a discovery call to understand your specific needs better. Would next week work for you?

Kind regards,
NexusFlow Sales Team""",

        "churn_reengagement": f"""Subject: We'd love to welcome you back, {customer_name}

Dear {customer_name},

I hope you're well. I'm reaching out because we value the relationship we built and wanted to share some exciting updates to the NexusFlow platform since we last spoke.

{context}

We've made significant improvements and I believe there may now be a great fit for your business. Would you be open to a brief call to reconnect?

Best wishes,
NexusFlow Customer Success Team"""
    }

    email_content = templates.get(reason, templates["stale_deal"])

    return json.dumps({
        "status": "draft_created",
        "customer_id": customer_id,
        "customer_name": customer_name,
        "email_type": reason,
        "draft": email_content,
        "created_at": datetime.now().isoformat(),
        "note": "Draft created — awaiting human approval before sending"
    }, indent=2)


@tool
def schedule_followup(customer_id: str, customer_name: str, task_description: str, due_date: str) -> str:
    """
    Schedule a CRM follow-up task by calling the real CRM API.

    Args:
        customer_id: CRM customer ID
        customer_name: Name of the customer
        task_description: What the rep needs to do
        due_date: When the task should be completed (YYYY-MM-DD)
    """
    data = _get(
        f"/api/contacts/{customer_id}/schedule",
    )

    # Use the real API endpoint
    try:
        r = requests.post(
            f"{CRM_BASE}/api/contacts/{customer_id}/schedule",
            params={"date": due_date, "note": task_description},
            timeout=5
        )
        r.raise_for_status()
        api_result = r.json()
    except Exception as e:
        api_result = {"error": str(e)}

    return json.dumps({
        "status": "task_scheduled",
        "customer_id": customer_id,
        "customer_name": customer_name,
        "description": task_description,
        "due_date": due_date,
        "crm_response": api_result,
        "created_at": datetime.now().isoformat()
    }, indent=2)


@tool
def flag_for_human_review(customer_id: str, customer_name: str, reason: str, priority: str, details: str) -> str:
    """
    Flag a situation for human review. Used for high-value deals or sensitive cases.

    Args:
        customer_id: CRM customer ID
        customer_name: Name of the customer
        reason: Why this needs human review
        priority: 'high', 'medium', or 'low'
        details: Full context for the reviewer
    """
    flag = {
        "flag_id": f"FLAG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "customer_id": customer_id,
        "customer_name": customer_name,
        "reason": reason,
        "priority": priority.upper(),
        "details": details,
        "flagged_by": "NexusFlow Agent",
        "flagged_at": datetime.now().isoformat(),
        "status": "pending_review"
    }

    # Save to human review log
    import os
    os.makedirs("logs", exist_ok=True)
    with open("logs/human_review_queue.jsonl", "a") as f:
        f.write(json.dumps(flag) + "\n")

    return json.dumps({
        "status": "flagged",
        "flag": flag,
        "message": f"[{priority.upper()}] {customer_name} flagged for human review — {reason}"
    }, indent=2)


@tool
def generate_weekly_report(period: str = "last_7_days") -> str:
    """
    Generate a weekly CRM summary using live data from the API.

    Args:
        period: Time period ('last_7_days' or 'last_30_days')
    """
    dashboard = _get("/api/dashboard")
    invoices = _get("/api/invoices", {"status": "Overdue"})

    if "error" in dashboard:
        return json.dumps(dashboard)

    overdue_list = invoices.get("invoices", [])

    return json.dumps({
        "report_type": "weekly_crm_summary",
        "period": period,
        "generated_at": datetime.now().isoformat(),
        "generated_by": "NexusFlow Agent",
        "pipeline_health": dashboard.get("pipeline", {}),
        "revenue": dashboard.get("revenue", {}),
        "contacts": dashboard.get("contacts", {}),
        "overdue_invoices": [
            {
                "id": i["id"],
                "company": i["company"],
                "amount_gbp": i["amount"],
                "due_date": i["due_date"],
                "days_overdue": _days_since(i["due_date"])
            }
            for i in overdue_list
        ],
        "status": "report_generated"
    }, indent=2)


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the NexusFlow knowledge base using the real ChromaDB vector store.
    Returns relevant content from sales playbook, product FAQ, onboarding guide,
    and company overview documents.

    Args:
        query: Natural language query
    """
    try:
        from rag.search import search
        results = search(query, k=4)

        return json.dumps({
            "query": query,
            "results": results,
            "count": len(results),
            "retrieved_at": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "query": query,
            "error": str(e),
            "results": [],
            "retrieved_at": datetime.now().isoformat()
        }, indent=2)