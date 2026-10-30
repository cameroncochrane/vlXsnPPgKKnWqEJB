# This script is constantly running. It checks the time every 60 seconds. When the time passes onto a new hour, 'main.py' is triggered.

import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from src.logger import setup_logging
from src.notification import send_email
from src.weekly_report import build_weekly_email

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 60

def main():
	script_dir = Path(__file__).resolve().parent
	logger.info("Scheduler started; main.py will run at the start of every hour.")
	last_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

	while True:
		time.sleep(CHECK_INTERVAL_SECONDS)  # Check the time every 60 seconds.
		current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
		if current_hour != last_hour: # When a new hour is reached 'main.py' is run.
			last_hour = current_hour
			if current_hour.weekday() == 0 and current_hour.hour == 9:
				try:
					send_email(subject="Weekly BTC Portfolio Update", message=build_weekly_email()) # Send portfolio update via email @ 9:00am every Monday
				except Exception: # A failed email must not stop the hourly loop
					logger.exception("Weekly email failed.")
			try:
				subprocess.Popen(
					[sys.executable, str(script_dir / "main.py")], # Invoke main.py here (it logs its own errors)
					cwd=script_dir,
				)
				logger.info("Started hourly run for %s.", current_hour.strftime("%Y-%m-%d %H:00"))
			except Exception:
				logger.exception("Couldn't start main.py.")

	
	
if __name__ == "__main__":
	setup_logging()
	main()
	# Invoke app.py (frontend) here
