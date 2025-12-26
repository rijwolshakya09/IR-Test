#!/usr/bin/env python3
"""
Automatic scheduler for the crawler using APScheduler.
Runs the crawler once per week (Sunday at midnight).
"""
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os

# Path to your virtual environment and crawler script
VENV_PATH = os.path.join(os.path.dirname(__file__), ".venv", "bin", "activate")
CRAWLER_SCRIPT = os.path.join(os.path.dirname(__file__), "crawler", "crawler.py")


# Function to run the crawler
def run_crawler():
    print("[Scheduler] Running crawler...")
    # Activate venv and run crawler
    subprocess.run(
        f"source {VENV_PATH} && python {CRAWLER_SCRIPT}", shell=True, check=False
    )
    print("[Scheduler] Crawler finished.")


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    # Schedule: every Sunday at midnight
    scheduler.add_job(run_crawler, "cron", day_of_week="sun", hour=0, minute=0)
    print("[Scheduler] Crawler scheduled to run every Sunday at midnight.")
    scheduler.start()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("[Scheduler] Scheduler stopped.")
