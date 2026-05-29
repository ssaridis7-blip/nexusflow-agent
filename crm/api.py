"""
Mock CRM API
=============
FastAPI-based mock CRM API serving synthetic business data.
Demonstrates CRM integration capabilities for the RAG Business Assistant.

Endpoints:
    GET  /api/contacts          - List all contacts (with optional filters)
    GET  /api/contacts/{id}     - Get specific contact
    GET  /api/interactions      - List interactions (with optional contact_id filter)
    GET  /api/invoices          - List invoices (with optional status filter)
    GET  /api/deals             - List deals (with optional stage filter)
    GET  /api/dashboard         - Aggregated business metrics
    POST /api/contacts/{id}/schedule - Schedule a follow-up for a contact
"""

import json
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

# ─── App Setup ───────────────────────────────────────────────────
app = FastAPI(
    title="NexusFlow CRM API",
    description="Mock CRM API for the RAG-Based AI Business Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Load Data ───────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_crm_data.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    CRM_DATA = json.load(f)


# ─── Health Check ────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": "NexusFlow CRM API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": [
            "/api/contacts",
            "/api/interactions",
            "/api/invoices",
            "/api/deals",
            "/api/dashboard"
        ]
    }


# ─── Contacts ────────────────────────────────────────────────────
@app.get("/api/contacts")
def get_contacts(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    status: Optional[str] = Query(None, description="Filter by lead status"),
    rep: Optional[str] = Query(None, description="Filter by assigned rep")
):
    """Retrieve all contacts with optional filters."""
    contacts = CRM_DATA["contacts"]

    if industry:
        contacts = [c for c in contacts if c["industry"].lower() == industry.lower()]
    if status:
        contacts = [c for c in contacts if c["lead_status"].lower() == status.lower()]
    if rep:
        contacts = [c for c in contacts if rep.lower() in c["assigned_rep"].lower()]

    return {"count": len(contacts), "contacts": contacts}


@app.get("/api/contacts/{contact_id}")
def get_contact(contact_id: str):
    """Retrieve a specific contact by ID."""
    contact = next((c for c in CRM_DATA["contacts"] if c["id"] == contact_id.upper()), None)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")

    # Enrich with related data
    interactions = [i for i in CRM_DATA["interactions"] if i["contact_id"] == contact["id"]]
    invoices = [i for i in CRM_DATA["invoices"] if i["contact_id"] == contact["id"]]
    deals = [d for d in CRM_DATA["deals"] if d["contact_id"] == contact["id"]]

    return {
        "contact": contact,
        "interactions": interactions,
        "invoices": invoices,
        "deals": deals
    }


# ─── Interactions ────────────────────────────────────────────────
@app.get("/api/interactions")
def get_interactions(
    contact_id: Optional[str] = Query(None, description="Filter by contact ID"),
    interaction_type: Optional[str] = Query(None, description="Filter by type (Email/Call/Meeting)"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment")
):
    """Retrieve interactions with optional filters."""
    interactions = CRM_DATA["interactions"]

    if contact_id:
        interactions = [i for i in interactions if i["contact_id"] == contact_id.upper()]
    if interaction_type:
        interactions = [i for i in interactions if i["type"].lower() == interaction_type.lower()]
    if sentiment:
        interactions = [i for i in interactions if i["sentiment"].lower() == sentiment.lower()]

    return {"count": len(interactions), "interactions": interactions}


# ─── Invoices ────────────────────────────────────────────────────
@app.get("/api/invoices")
def get_invoices(
    status: Optional[str] = Query(None, description="Filter by status (Paid/Pending/Overdue/Draft)"),
    company: Optional[str] = Query(None, description="Filter by company name")
):
    """Retrieve invoices with optional filters."""
    invoices = CRM_DATA["invoices"]

    if status:
        invoices = [i for i in invoices if i["status"].lower() == status.lower()]
    if company:
        invoices = [i for i in invoices if company.lower() in i["company"].lower()]

    return {"count": len(invoices), "invoices": invoices}


# ─── Deals ───────────────────────────────────────────────────────
@app.get("/api/deals")
def get_deals(
    stage: Optional[str] = Query(None, description="Filter by deal stage"),
    rep: Optional[str] = Query(None, description="Filter by sales rep")
):
    """Retrieve deals with optional filters."""
    deals = CRM_DATA["deals"]

    if stage:
        deals = [d for d in deals if d["stage"].lower() == stage.lower()]
    if rep:
        deals = [d for d in deals if rep.lower() in d["rep"].lower()]

    return {"count": len(deals), "deals": deals}


# ─── Dashboard / Analytics ───────────────────────────────────────
@app.get("/api/dashboard")
def get_dashboard():
    """Aggregated business metrics and KPIs."""
    contacts = CRM_DATA["contacts"]
    invoices = CRM_DATA["invoices"]
    deals = CRM_DATA["deals"]
    interactions = CRM_DATA["interactions"]

    # Revenue metrics
    total_invoiced = sum(i["amount"] for i in invoices)
    total_paid = sum(i["amount"] for i in invoices if i["status"] == "Paid")
    total_pending = sum(i["amount"] for i in invoices if i["status"] == "Pending")
    total_overdue = sum(i["amount"] for i in invoices if i["status"] == "Overdue")

    # Pipeline metrics
    active_deals = [d for d in deals if d["stage"] not in ["Lost"]]
    pipeline_value = sum(d["value"] for d in active_deals)
    weighted_pipeline = sum(d["value"] * d["probability"] / 100 for d in active_deals)

    # Contact metrics
    status_counts = {}
    for c in contacts:
        status = c["lead_status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    # Interaction metrics
    sentiment_counts = {}
    for i in interactions:
        sentiment = i["sentiment"]
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1

    return {
        "revenue": {
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_pending": total_pending,
            "total_overdue": total_overdue
        },
        "pipeline": {
            "active_deals": len(active_deals),
            "total_pipeline_value": pipeline_value,
            "weighted_pipeline_value": round(weighted_pipeline, 2),
            "avg_deal_probability": round(sum(d["probability"] for d in active_deals) / len(active_deals), 1)
        },
        "contacts": {
            "total": len(contacts),
            "by_status": status_counts,
            "avg_lead_score": round(sum(c["lead_score"] for c in contacts) / len(contacts), 1)
        },
        "interactions": {
            "total": len(interactions),
            "by_sentiment": sentiment_counts
        }
    }


# ─── Schedule Follow-up ─────────────────────────────────────────
@app.post("/api/contacts/{contact_id}/schedule")
def schedule_followup(
    contact_id: str,
    date: str = Query(..., description="Follow-up date (YYYY-MM-DD)"),
    note: str = Query("", description="Follow-up note")
):
    """Schedule a follow-up for a contact (mock operation)."""
    contact = next((c for c in CRM_DATA["contacts"] if c["id"] == contact_id.upper()), None)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")

    return {
        "status": "scheduled",
        "contact": f"{contact['first_name']} {contact['last_name']}",
        "company": contact["company"],
        "follow_up_date": date,
        "note": note,
        "created_at": datetime.now().isoformat()
    }


# ─── Run Server ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("\n=== Starting NexusFlow CRM API ===")
    print("API docs available at: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
