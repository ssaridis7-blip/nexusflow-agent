# NexusFlow Agent

Autonomous CRM AI Agent built with LangGraph, GPT-4o, ChromaDB, FastAPI, and Streamlit.

> Extended from BSc Dissertation — RAG-Based AI Business Assistant  
> University of Derby, Module 6CM995, 2026  
> Author: Saridis Stavros

---

## What It Does

NexusFlow Agent monitors a CRM system autonomously, makes business decisions, and takes action — without human input.

Every hour it:
- Scans for overdue invoices, stale deals, churned customers, and uncontacted leads
- Applies business rules to decide what action is needed
- Drafts personalised follow-up emails
- Schedules tasks in the CRM
- Flags high-value situations for human review
- Sends an email report to the manager
- Logs every decision with full reasoning

---

## Architecture
APScheduler (hourly trigger)
|
LangGraph Agent (monitor → decide → report)
|
┌────┴────────────────┐
|                     |
FastAPI CRM API     ChromaDB RAG
(7 endpoints)       (164 vectors)
|
LangSmith Tracing
|
Streamlit Dashboard

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | LangGraph |
| LLM | GPT-4o |
| Embeddings | text-embedding-3-small |
| Vector Store | ChromaDB |
| CRM API | FastAPI |
| Observability | LangSmith |
| Dashboard | Streamlit |
| Scheduler | APScheduler |
| Notifications | Gmail SMTP |
| Language | Python 3.12 |

---

## Project Structure
nexusflow-agent/
├── agent/
│   ├── graph.py        # LangGraph agent definition
│   ├── nodes.py        # Monitor, decide, report nodes
│   ├── tools.py        # 8 agent tools
│   ├── prompts.py      # System prompts and business rules
│   └── memory.py       # LangGraph checkpointer
├── crm/
│   ├── api.py          # FastAPI CRM (7 endpoints)
│   └── synthetic_data.json
├── rag/
│   ├── search.py       # ChromaDB search wrapper
│   ├── pipeline.py     # Full RAG pipeline
│   ├── chroma_db/      # Pre-built vector store
│   └── knowledge_base/ # 4 NexusFlow documents
├── dashboard/
│   └── app.py          # Streamlit dashboard
├── notifications/
│   └── email.py        # Gmail SMTP notifications
├── scheduler/
│   └── runner.py       # APScheduler hourly runner
├── logs/
│   └── agent_actions.jsonl
├── tests/
│   └── test_phase1.py  # 18 passing tests
└── main.py             # Manual run entry point

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/ssaridis7-blip/nexusflow-agent.git
cd nexusflow-agent
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**
```bash
cp .env.example .env
# Add your API keys to .env
```

**5. Run the CRM API** (Terminal 1)
```bash
python crm/api.py
```

**6. Run the agent** (Terminal 2)
```bash
python main.py
```

**7. Open the dashboard** (Terminal 2)
```bash
streamlit run dashboard/app.py
```

---

## Environment Variables
OPENAI_API_KEY=your-openai-key
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=nexusflow-agent
LANGCHAIN_TRACING_V2=true
GMAIL_ADDRESS=your-gmail@gmail.com
GMAIL_APP_PASSWORD=your-app-password

---

## Running Tests

```bash
python -m pytest tests/ -v
```

18 tests covering tools, graph structure, state management, and prompts.

---

## Autonomous Scheduler

To run the agent automatically every hour:

```bash
python -m scheduler.runner
```

---

## Related Project

This agent extends the BSc dissertation:  
[RAG-Based AI Business Assistant](https://github.com/ssaridis7-blip/bsc-dissertation-2026)

---

## CV Summary
NexusFlow Agent | Python, LangGraph, GPT-4o, ChromaDB, FastAPI, LangSmith

Built an autonomous CRM agent using LangGraph that monitors customer
data, makes business decisions, and executes actions without human input
Implemented 8 tools including invoice monitoring, deal tracking,
automated email drafting, and RAG-powered knowledge retrieval
Integrated LangSmith observability for full agent decision tracing
Extended BSc dissertation RAG system into a production-ready agentic architecture
Streamlit dashboard with live pipeline metrics, human review queue, and email inbox