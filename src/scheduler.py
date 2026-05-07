import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import schedule
import time
import logging
from datetime import datetime
from src.etl_pipeline import run_pipeline
from config.config import FETCH_INTERVAL_MINUTES

LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "pipeline.log")

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def scheduled_job():
    """Wrapper that runs the pipeline and logs the result."""
    print(f"\n⏰ Scheduled run starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("Scheduled pipeline run started.")

    try:
        loaded, alerts = run_pipeline()
        logging.info(f"Pipeline completed. Loaded: {loaded}, Alerts: {len(alerts)}")
        print(f"✅ Run complete — {loaded} records loaded, {len(alerts)} alerts.\n")
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        print(f"❌ Pipeline failed: {e}\n")


def start_scheduler():
    """Start the scheduler — runs pipeline every N minutes from config."""
    print(f"\n🚀 Scheduler started.")
    print(f"   Pipeline will run every {FETCH_INTERVAL_MINUTES} minute(s).")
    print(f"   Press Ctrl+C to stop.\n")

    # Run immediately on start
    scheduled_job()

    # Then schedule recurring runs
    schedule.every(FETCH_INTERVAL_MINUTES).minutes.do(scheduled_job)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    start_scheduler()