#!/usr/bin/env python3
"""
Weekly scheduler for the crawler (Sunday at midnight).
"""
import subprocess
import time
import os
from apscheduler.schedulers.background import BackgroundScheduler

VENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".venv", "bin", "activate")
CRAWLER_SCRIPT = os.path.join(os.path.dirname(__file__), "playwright_crawler.py")


def run_crawler():
    print("[Scheduler] Running crawler...")
    subprocess.run(
        f"source {VENV_PATH} && python {CRAWLER_SCRIPT}",
        shell=True,
        check=False,
    )
    print("[Scheduler] Crawler finished.")


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_crawler, "cron", day_of_week="sun", hour=0, minute=0)
    print("[Scheduler] Crawler scheduled to run every Sunday at midnight.")
    scheduler.start()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("[Scheduler] Scheduler stopped.")
