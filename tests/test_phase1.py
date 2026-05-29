"""
NexusFlow Agent — Phase 1 Tests
Tests the tools and graph structure without requiring API keys.

Run with: pytest tests/ -v
"""

import json
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────
# TOOL TESTS
# ─────────────────────────────────────────────

class TestMonitoringTools:
    
    def test_get_overdue_invoices_returns_valid_json(self):
        from agent.tools import get_overdue_invoices
        result = get_overdue_invoices.invoke({})
        data = json.loads(result)
        
        assert "overdue_invoices" in data
        assert "total_overdue_gbp" in data
        assert isinstance(data["overdue_invoices"], list)
        assert len(data["overdue_invoices"]) > 0
    
    def test_overdue_invoices_have_required_fields(self):
        from agent.tools import get_overdue_invoices
        result = json.loads(get_overdue_invoices.invoke({}))
        
        required_fields = ["invoice_id", "contact_id", "company",
                          "amount_gbp", "days_overdue", "status"]
        for invoice in result["overdue_invoices"]:
            for field in required_fields:
                assert field in invoice, f"Missing field: {field}"
    
    def test_get_stale_deals_returns_valid_json(self):
        from agent.tools import get_stale_deals
        result = get_stale_deals.invoke({})
        data = json.loads(result)
        
        assert "stale_deals" in data
        assert isinstance(data["stale_deals"], list)
        assert len(data["stale_deals"]) > 0
    
    def test_stale_deals_all_exceed_14_days(self):
        from agent.tools import get_stale_deals
        result = json.loads(get_stale_deals.invoke({}))
        
        for deal in result["stale_deals"]:
            assert deal["days_stale"] >= 14, \
                f"Deal {deal['deal_id']} has only {deal['days_stale']} days stale"
    
    def test_get_unengaged_leads_returns_valid_json(self):
        from agent.tools import get_unengaged_leads
        result = get_unengaged_leads.invoke({})
        data = json.loads(result)
        
        assert "uncontacted_leads" in data
        assert "churned_no_reengagement" in data


class TestActionTools:
    
    def test_draft_followup_email_overdue_invoice(self):
        from agent.tools import draft_followup_email
        result = draft_followup_email.invoke({
            "customer_name": "David Okafor",
            "customer_id": "C003",
            "reason": "overdue_invoice",
            "context": "Invoice INV-007 for £45,000 is 23 days overdue."
        })
        data = json.loads(result)
        
        assert data["status"] == "draft_created"
        assert "draft" in data
        assert "David Okafor" in data["draft"]
        assert data["customer_id"] == "C003"
    
    def test_draft_followup_email_all_reasons(self):
        from agent.tools import draft_followup_email
        
        reasons = ["overdue_invoice", "stale_deal", "lead_nurture", "churn_reengagement"]
        for reason in reasons:
            result = draft_followup_email.invoke({
                "customer_name": "Test Customer",
                "customer_id": "C001",
                "reason": reason,
                "context": "Test context"
            })
            data = json.loads(result)
            assert data["status"] == "draft_created", f"Failed for reason: {reason}"
    
    def test_schedule_followup_creates_task_id(self):
        from agent.tools import schedule_followup
        result = schedule_followup.invoke({
            "customer_id": "C003",
            "customer_name": "David Okafor",
            "task_description": "Call to discuss overdue invoice INV-007",
            "due_date": "2026-06-04"
        })
        data = json.loads(result)
        
        assert data["status"] == "task_scheduled"
        assert "customer_id" in data
        assert data["customer_id"] == "C003"
    
    def test_flag_for_human_review(self):
        from agent.tools import flag_for_human_review
        result = flag_for_human_review.invoke({
            "customer_id": "C005",
            "customer_name": "Ahmed Hassan",
            "reason": "High-value deal £120k stale for 18 days",
            "priority": "high",
            "details": "DEAL-004 requires senior account management attention"
        })
        data = json.loads(result)
        
        assert data["status"] == "flagged"
        assert data["flag"]["priority"] == "HIGH"
        assert "flag_id" in data["flag"]
    
    def test_generate_weekly_report(self):
        from agent.tools import generate_weekly_report
        result = generate_weekly_report.invoke({})
        data = json.loads(result)
        
        assert data["status"] == "report_generated"
        assert "pipeline_health" in data
        assert "revenue" in data
        assert "overdue_invoices" in data
    
    def test_search_knowledge_base(self):
        from agent.tools import search_knowledge_base
        result = search_knowledge_base.invoke({
            "query": "how to follow up on overdue invoices"
        })
        data = json.loads(result)
        
        assert "results" in data
        assert len(data["results"]) > 0
        assert "relevance_score" in data["results"][0]


# ─────────────────────────────────────────────
# GRAPH STRUCTURE TESTS
# ─────────────────────────────────────────────

class TestGraphStructure:
    
    def test_graph_compiles_without_error(self):
        from agent.graph import build_agent_graph
        graph = build_agent_graph()
        assert graph is not None
    
    def test_initial_state_has_correct_keys(self):
        from agent.graph import get_initial_state
        state = get_initial_state()
        
        required_keys = ["messages", "phase", "cycle_start", 
                        "monitoring_results", "actions_taken", 
                        "decision_reasoning", "final_report"]
        for key in required_keys:
            assert key in state, f"Missing state key: {key}"
    
    def test_initial_state_phase_is_start(self):
        from agent.graph import get_initial_state
        state = get_initial_state()
        assert state["phase"] == "start"
    
    def test_all_tools_are_registered(self):
        from agent.nodes import ALL_TOOLS, TOOL_MAP
        
        expected_tools = [
            "get_overdue_invoices",
            "get_stale_deals", 
            "get_unengaged_leads",
            "draft_followup_email",
            "schedule_followup",
            "flag_for_human_review",
            "generate_weekly_report",
            "search_knowledge_base"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in TOOL_MAP, f"Tool not registered: {tool_name}"
    
    def test_tool_count(self):
        from agent.nodes import ALL_TOOLS
        assert len(ALL_TOOLS) == 8, f"Expected 8 tools, got {len(ALL_TOOLS)}"


# ─────────────────────────────────────────────
# PROMPT TESTS
# ─────────────────────────────────────────────

class TestPrompts:
    
    def test_all_prompts_are_non_empty(self):
        from agent.prompts import (
            AGENT_SYSTEM_PROMPT, MONITOR_PROMPT, 
            DECISION_PROMPT, REPORT_PROMPT
        )
        
        prompts = {
            "AGENT_SYSTEM_PROMPT": AGENT_SYSTEM_PROMPT,
            "MONITOR_PROMPT": MONITOR_PROMPT,
            "DECISION_PROMPT": DECISION_PROMPT,
            "REPORT_PROMPT": REPORT_PROMPT,
        }
        
        for name, prompt in prompts.items():
            assert len(prompt) > 100, f"Prompt too short: {name}"
    
    def test_system_prompt_contains_business_rules(self):
        from agent.prompts import AGENT_SYSTEM_PROMPT
        
        assert "overdue" in AGENT_SYSTEM_PROMPT.lower()
        assert "stale" in AGENT_SYSTEM_PROMPT.lower()
        assert "£50,000" in AGENT_SYSTEM_PROMPT or "50,000" in AGENT_SYSTEM_PROMPT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])