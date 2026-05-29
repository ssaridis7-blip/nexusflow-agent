"""
NexusFlow Agent — Streamlit Dashboard (Phase 5 - Professional UI)
Clean light theme, professional typography, no emojis.
"""

import streamlit as st
import json
import os
import requests
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="NexusFlow Agent Dashboard",
    page_icon="assets/logo.png" if os.path.exists("assets/logo.png") else None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# PROFESSIONAL LIGHT THEME
# ─────────────────────────────────────────────

st.markdown("""
<style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f8f9fc; color: #1a1d23; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1d23;
        border-right: none;
    }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stMarkdown p { color: #94a3b8 !important; }

    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Top header bar */
    .header-bar {
        background-color: #ffffff;
        border-bottom: 1px solid #e2e8f0;
        padding: 20px 0 16px 0;
        margin-bottom: 24px;
    }
    .header-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1a1d23;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        font-size: 0.875rem;
        color: #64748b;
        margin: 4px 0 0 0;
    }

    /* Section titles */
    .section-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748b;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #e2e8f0;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    [data-testid="stMetricValue"] {
        color: #1a1d23 !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* Cards */
    .card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .card-critical {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #dc2626;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .card-warning {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #d97706;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .card-email {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #2563eb;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .badge-critical { background-color: #fee2e2; color: #dc2626; }
    .badge-warning { background-color: #fef3c7; color: #d97706; }
    .badge-success { background-color: #dcfce7; color: #16a34a; }
    .badge-info { background-color: #dbeafe; color: #2563eb; }
    .badge-purple { background-color: #ede9fe; color: #7c3aed; }
    .badge-gray { background-color: #f1f5f9; color: #64748b; }

    /* Cycle feed item */
    .feed-item {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .feed-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #1a1d23;
        margin: 0 0 4px 0;
    }
    .feed-meta {
        font-size: 0.78rem;
        color: #94a3b8;
        margin: 0 0 12px 0;
    }

    /* Customer name */
    .customer-name {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1a1d23;
    }
    .customer-id {
        font-size: 0.78rem;
        color: #94a3b8;
        margin-left: 6px;
    }
    .flag-reason {
        font-size: 0.875rem;
        color: #374151;
        margin: 8px 0 4px 0;
    }
    .flag-detail {
        font-size: 0.8rem;
        color: #6b7280;
        line-height: 1.5;
    }
    .flag-time {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 8px;
    }

    /* Email draft */
    .email-draft {
        background-color: #f8f9fc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 16px;
        font-family: 'Courier New', monospace;
        font-size: 0.82rem;
        color: #374151;
        white-space: pre-wrap;
        line-height: 1.6;
        margin-top: 12px;
    }

    /* Expander styling */
    [data-testid="stExpander"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* Sidebar nav */
    .sidebar-logo {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff !important;
        letter-spacing: -0.3px;
    }
    .sidebar-tagline {
        font-size: 0.78rem;
        color: #64748b !important;
        margin-top: 2px;
    }
    .sidebar-section {
        font-size: 0.68rem;
        font-weight: 600;
        color: #475569 !important;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 20px 0 8px 0;
    }
    .sidebar-stat {
        font-size: 0.875rem;
        color: #cbd5e1 !important;
        padding: 6px 0;
        border-bottom: 1px solid #2d3250;
        display: flex;
        justify-content: space-between;
    }
    .sidebar-stat-value {
        font-weight: 600;
        color: #ffffff !important;
    }
    .status-dot-green {
        display: inline-block;
        width: 7px;
        height: 7px;
        background: #22c55e;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
    }
    .status-dot-red {
        display: inline-block;
        width: 7px;
        height: 7px;
        background: #ef4444;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
    }

    /* Report text */
    .report-text {
        font-size: 0.875rem;
        color: #374151;
        line-height: 1.7;
    }

    /* Divider */
    .divider { border: none; border-top: 1px solid #e2e8f0; margin: 24px 0; }

    /* Toggle label fix */
    [data-testid="stToggle"] label { color: #94a3b8 !important; font-size: 0.8rem; }

    /* Selectbox */
    [data-testid="stSelectbox"] {
        background-color: #ffffff;
    }

    /* Button overrides */
    .stButton button {
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        padding: 4px 14px;
        border: 1px solid #e2e8f0;
        background-color: #ffffff;
        color: #374151;
    }
    .stButton button:hover {
        background-color: #f1f5f9;
        border-color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────

LOGS_PATH = Path("logs/agent_actions.jsonl")
REVIEW_PATH = Path("logs/human_review_queue.jsonl")
CRM_BASE = "http://localhost:8000"


@st.cache_data(ttl=60)
def load_agent_logs() -> list:
    if not LOGS_PATH.exists():
        return []
    cycles = []
    with open(LOGS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    cycles.append(json.loads(line))
                except Exception:
                    pass
    return list(reversed(cycles))


@st.cache_data(ttl=60)
def load_review_queue() -> list:
    if not REVIEW_PATH.exists():
        return []
    flags = []
    with open(REVIEW_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    flags.append(json.loads(line))
                except Exception:
                    pass
    return list(reversed(flags))


@st.cache_data(ttl=60)
def load_crm_dashboard() -> dict:
    try:
        r = requests.get(f"{CRM_BASE}/api/dashboard", timeout=3)
        return r.json()
    except Exception:
        return {}


def get_all_drafted_emails(cycles: list) -> list:
    emails = []
    for cycle in cycles:
        for action in cycle.get("actions_taken", []):
            if action["tool"] == "draft_followup_email":
                try:
                    result = json.loads(action["result"])
                    result["cycle_id"] = cycle.get("cycle_id", "")
                    result["cycle_time"] = cycle.get("cycle_start", "")
                    emails.append(result)
                except Exception:
                    pass
    return emails


def fmt_time(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return iso_str[:16].replace("T", " ")


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────

cycles = load_agent_logs()
review_queue = load_review_queue()
crm_data = load_crm_dashboard()
emails = get_all_drafted_emails(cycles)
total_actions = sum(len(c.get("actions_taken", [])) for c in cycles)
auto_refresh = True


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown('<p class="sidebar-logo">NexusFlow Agent</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-tagline">Autonomous CRM Intelligence</p>', unsafe_allow_html=True)

    st.markdown("---")

    # CRM status
    crm_online = bool(crm_data)
    if crm_online:
        st.markdown('<span class="status-dot-green"></span><span style="color:#94a3b8; font-size:0.8rem;">CRM API online</span>',
                   unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-dot-red"></span><span style="color:#94a3b8; font-size:0.8rem;">CRM API offline</span>',
                   unsafe_allow_html=True)

    st.markdown('<p class="sidebar-section">Overview</p>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="sidebar-stat">
        <span>Cycles run</span>
        <span class="sidebar-stat-value">{len(cycles)}</span>
    </div>
    <div class="sidebar-stat">
        <span>Total actions</span>
        <span class="sidebar-stat-value">{total_actions}</span>
    </div>
    <div class="sidebar-stat">
        <span style="color:#ef4444;">Pending reviews</span>
        <span class="sidebar-stat-value" style="color:#ef4444;">{len(review_queue)}</span>
    </div>
    <div class="sidebar-stat">
        <span>Drafted emails</span>
        <span class="sidebar-stat-value">{len(emails)}</span>
    </div>
    """, unsafe_allow_html=True)

    if cycles:
        st.markdown('<p class="sidebar-section">Last Run</p>', unsafe_allow_html=True)
        last = cycles[0]
        st.markdown(f'<p style="color:#94a3b8; font-size:0.8rem;">{fmt_time(last.get("cycle_start",""))}</p>',
                   unsafe_allow_html=True)
        st.markdown(f'<p style="color:#94a3b8; font-size:0.78rem;">{len(last.get("actions_taken",[]))} actions taken</p>',
                   unsafe_allow_html=True)

    st.markdown("---")
    auto_refresh = st.toggle("Auto-refresh (60s)", value=True)
    st.markdown("---")
    st.markdown('<p style="color:#475569; font-size:0.72rem;">Built with LangGraph + GPT-4o<br>University of Derby, 2026</p>',
               unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown('<p class="header-title">Agent Dashboard</p>', unsafe_allow_html=True)
st.markdown(f'<p class="header-subtitle">Autonomous CRM monitoring — last updated {datetime.now().strftime("%d %b %Y, %H:%M:%S")}</p>',
           unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PIPELINE METRICS
# ─────────────────────────────────────────────

st.markdown('<p class="section-title">Pipeline Health</p>', unsafe_allow_html=True)

if crm_data:
    pipeline = crm_data.get("pipeline", {})
    revenue = crm_data.get("revenue", {})

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Pipeline Value", f"£{pipeline.get('total_pipeline_value', 0):,.0f}")
    with c2:
        st.metric("Active Deals", pipeline.get("active_deals", 0))
    with c3:
        overdue = revenue.get("total_overdue", 0)
        st.metric("Overdue Amount", f"£{overdue:,.0f}",
                 delta=f"-£{overdue:,.0f}" if overdue > 0 else None,
                 delta_color="inverse")
    with c4:
        st.metric("Avg Probability", f"{pipeline.get('avg_deal_probability', 0)}%")
else:
    st.warning("CRM API is not running. Start it with: python crm/api.py")

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# REVIEW QUEUE + ACTIVITY FEED
# ─────────────────────────────────────────────

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown(f'<p class="section-title">Human Review Queue &nbsp;<span class="badge badge-critical">{len(review_queue)}</span></p>',
               unsafe_allow_html=True)

    if not review_queue:
        st.markdown('<div class="card"><p style="color:#16a34a; font-size:0.875rem; margin:0;">No items require attention.</p></div>',
                   unsafe_allow_html=True)
    else:
        for flag in review_queue[:10]:
            priority = flag.get("priority", "MEDIUM")
            card_class = "card-critical" if priority == "HIGH" else "card-warning"
            badge_class = "badge-critical" if priority == "HIGH" else "badge-warning"

            st.markdown(f"""
            <div class="{card_class}">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:10px;">
                    <span class="badge {badge_class}">{priority}</span>
                    <span class="customer-name">{flag.get('customer_name', 'Unknown')}</span>
                    <span class="customer-id">{flag.get('customer_id', '')}</span>
                </div>
                <p class="flag-reason"><b>Reason:</b> {flag.get('reason', '')}</p>
                <p class="flag-detail">{flag.get('details', '')}</p>
                <p class="flag-time">{fmt_time(flag.get('flagged_at', ''))}</p>
            </div>
            """, unsafe_allow_html=True)

with col_right:
    st.markdown('<p class="section-title">Agent Activity Feed</p>', unsafe_allow_html=True)

    if not cycles:
        st.markdown('<div class="card"><p style="color:#94a3b8; font-size:0.875rem; margin:0;">No cycles run yet.</p></div>',
                   unsafe_allow_html=True)
    else:
        for cycle in cycles[:6]:
            actions = cycle.get("actions_taken", [])
            n_flags = sum(1 for a in actions if a["tool"] == "flag_for_human_review")
            n_emails = sum(1 for a in actions if a["tool"] == "draft_followup_email")
            n_tasks = sum(1 for a in actions if a["tool"] == "schedule_followup")
            n_search = sum(1 for a in actions if a["tool"] == "search_knowledge_base")

            badges = ""
            if n_flags:
                badges += f'<span class="badge badge-critical" style="margin-right:4px;">{n_flags} flagged</span>'
            if n_emails:
                badges += f'<span class="badge badge-info" style="margin-right:4px;">{n_emails} emails</span>'
            if n_tasks:
                badges += f'<span class="badge badge-success" style="margin-right:4px;">{n_tasks} tasks</span>'
            if n_search:
                badges += f'<span class="badge badge-purple" style="margin-right:4px;">RAG search</span>'

            st.markdown(f"""
            <div class="feed-item">
                <p class="feed-title">{cycle.get('cycle_id', '')}</p>
                <p class="feed-meta">{fmt_time(cycle.get('cycle_start', ''))} &nbsp;·&nbsp; {len(actions)} actions</p>
                {badges}
            </div>
            """, unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DRAFTED EMAILS INBOX
# ─────────────────────────────────────────────

st.markdown(f'<p class="section-title">Drafted Emails &nbsp;<span class="badge badge-info">{len(emails)}</span></p>',
           unsafe_allow_html=True)

if not emails:
    st.markdown('<div class="card"><p style="color:#94a3b8; font-size:0.875rem; margin:0;">No drafted emails yet.</p></div>',
               unsafe_allow_html=True)
else:
    email_types = ["All"] + sorted(set(e.get("email_type", "unknown") for e in emails))
    col_filter, _ = st.columns([2, 5])
    with col_filter:
        selected_type = st.selectbox("Filter by type", email_types,
                                    label_visibility="collapsed")

    filtered = emails if selected_type == "All" else [
        e for e in emails if e.get("email_type") == selected_type
    ]

    for i, email in enumerate(filtered[:20]):
        customer = email.get("customer_name", "Unknown")
        email_type = email.get("email_type", "unknown").replace("_", " ").title()
        draft = email.get("draft", "")
        cycle_time = email.get("cycle_time", "")

        with st.expander(f"{customer}  —  {email_type}  |  {fmt_time(cycle_time)}"):
            st.markdown(f'<div class="email-draft">{draft}</div>', unsafe_allow_html=True)
            col_a, col_b, col_c = st.columns([1, 1, 5])
            with col_a:
                st.button("Approve", key=f"approve_{i}",
                         help="Phase 6: Wires to Gmail send")
            with col_b:
                st.button("Discard", key=f"discard_{i}")

st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# LATEST REPORT
# ─────────────────────────────────────────────

st.markdown('<p class="section-title">Latest Cycle Report</p>', unsafe_allow_html=True)

if cycles:
    latest = cycles[0]
    summary = latest.get("summary", "No summary available.")

    col_report, col_meta = st.columns([3, 1], gap="large")

    with col_report:
        st.markdown(f'<div class="card"><div class="report-text">{summary}</div></div>',
                   unsafe_allow_html=True)

    with col_meta:
        st.markdown(f"""
        <div class="card">
            <p style="font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin:0 0 4px 0;">Cycle ID</p>
            <p style="font-size:0.8rem; color:#1a1d23; font-weight:500; margin:0 0 14px 0;">{latest.get('cycle_id', '')}</p>

            <p style="font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin:0 0 4px 0;">Started</p>
            <p style="font-size:0.8rem; color:#1a1d23; margin:0 0 14px 0;">{fmt_time(latest.get('cycle_start',''))}</p>

            <p style="font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin:0 0 4px 0;">Ended</p>
            <p style="font-size:0.8rem; color:#1a1d23; margin:0 0 14px 0;">{fmt_time(latest.get('cycle_end',''))}</p>

            <p style="font-size:0.7rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin:0 0 4px 0;">Actions Taken</p>
            <p style="font-size:1.4rem; color:#1a1d23; font-weight:700; margin:0;">{len(latest.get('actions_taken', []))}</p>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────────

if auto_refresh:
    import time
    time.sleep(60)
    st.rerun()