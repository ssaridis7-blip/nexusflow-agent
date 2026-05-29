"""
NexusFlow Agent — Main Runner
Run this to test the agent manually: python main.py

For automated scheduled runs: python -m scheduler.runner
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()


def check_environment():
    """Verify required environment variables are set before running."""
    required = ["OPENAI_API_KEY"]
    optional = ["LANGSMITH_API_KEY", "LANGSMITH_PROJECT", "SENDGRID_API_KEY"]
    
    missing_required = [k for k in required if not os.getenv(k)]
    missing_optional = [k for k in optional if not os.getenv(k)]
    
    if missing_required:
        print("❌ Missing required environment variables:")
        for k in missing_required:
            print(f"   - {k}")
        print("\nCreate a .env file with your API keys. See .env.example")
        return False
    
    if missing_optional:
        print("⚠️  Optional environment variables not set (some features disabled):")
        for k in missing_optional:
            print(f"   - {k}")
    
    return True


def main():
    print("=" * 60)
    print("  NexusFlow Autonomous CRM Agent")
    print("  Phase 1 — Manual Test Run")
    print("=" * 60)
    
    if not check_environment():
        return
    
    # LangSmith tracing (if configured)
    if os.getenv("LANGSMITH_API_KEY"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "nexusflow-agent")
        print("✅ LangSmith tracing enabled")
    
    print("\n[AGENT] Starting agent cycle...\n")
    
    # Import here so env vars are set first
    from agent.graph import run_agent_cycle
    
    try:
        final_state = run_agent_cycle()
        
        # Pretty print the final report
        if final_state.get("final_report"):
            report = final_state["final_report"]
            print(f"\n📊 Cycle ID: {report.get('cycle_id')}")
            print(f"⏱️  Duration: {report.get('cycle_start')} → {report.get('cycle_end')}")
            print(f"\n📋 Actions taken: {len(report.get('actions_taken', []))}")
            
            for action in report.get("actions_taken", []):
                print(f"   • {action['tool']} — {action['timestamp']}")
        
        # Save report to logs
        os.makedirs("logs", exist_ok=True)
        with open("logs/agent_actions.jsonl", "a") as f:
            if final_state.get("final_report"):
                f.write(json.dumps(final_state["final_report"]) + "\n")
        
        # Send email notification
        from notifications.email import send_cycle_report
        if final_state.get("final_report"):
            send_cycle_report(final_state["final_report"])

        print("\n✅ Cycle complete. Report saved to logs/agent_actions.jsonl")
        
    except Exception as e:
        print(f"\n❌ Agent cycle failed: {e}")
        raise


if __name__ == "__main__":
    main()