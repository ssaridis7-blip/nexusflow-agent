"""
NexusFlow Agent — APScheduler Runner (Phase 4)
Runs the agent automatically on a schedule.
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nexusflow.scheduler")


def run_cycle():
    """One full agent cycle — called by the scheduler."""
    print(f"\n{'='*60}")
    print(f"[SCHEDULER] Starting scheduled cycle — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    try:
        # Run the agent
        from agent.graph import run_agent_cycle
        final_state = run_agent_cycle()

        # Save to log
        os.makedirs("logs", exist_ok=True)
        if final_state.get("final_report"):
            with open("logs/agent_actions.jsonl", "a") as f:
                f.write(json.dumps(final_state["final_report"]) + "\n")

        # Send email notification if there are flags
        from notifications.email import send_cycle_report
        if final_state.get("final_report"):
            send_cycle_report(final_state["final_report"])

        print(f"[SCHEDULER] ✅ Cycle complete")

    except Exception as e:
        print(f"[SCHEDULER] ❌ Cycle failed: {e}")
        log.error(f"Agent cycle failed: {e}", exc_info=True)


def start_scheduler(interval_hours: int = 1):
    """
    Start the APScheduler. Runs the agent every hour by default.
    Change interval_hours to 24 for once-daily runs.
    """
    scheduler = BlockingScheduler()

    scheduler.add_job(
        run_cycle,
        trigger=IntervalTrigger(hours=interval_hours),
        id="nexusflow_agent_cycle",
        name="NexusFlow CRM Agent",
        replace_existing=True,
        max_instances=1       # Never run two cycles at once
    )

    print(f"""
{'='*60}
  NexusFlow Agent Scheduler
  Running every {interval_hours} hour(s)
  Press Ctrl+C to stop
{'='*60}
    """)

    # Run once immediately on startup
    print("[SCHEDULER] Running initial cycle now...")
    run_cycle()

    # Then start the schedule
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[SCHEDULER] Stopped.")


if __name__ == "__main__":
    # For testing: run every 2 minutes instead of every hour
    # Change to start_scheduler(interval_hours=1) for production
    start_scheduler(interval_hours=1)