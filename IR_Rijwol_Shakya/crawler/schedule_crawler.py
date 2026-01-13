#!/usr/bin/env python3
"""
Weekly scheduler for the crawler (Sunday at midnight).
"""
import os
import subprocess
import sys
import time

from apscheduler.schedulers.background import BackgroundScheduler

BASE_DIR = os.path.dirname(__file__)
VENV_PY = os.path.join(BASE_DIR, "..", ".venv", "bin", "python")
CRAWLER_SCRIPT = os.path.join(BASE_DIR, "crawler.py")


def run_crawler():
    print("[Scheduler] Running crawler...")
    python_bin = VENV_PY if os.path.exists(VENV_PY) else sys.executable
    subprocess.run([python_bin, CRAWLER_SCRIPT], check=False)
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
