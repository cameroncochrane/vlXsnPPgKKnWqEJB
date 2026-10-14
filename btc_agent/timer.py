# This script is constantly running. It checks the time every 60 seconds. When the time passes onto a new hour, 'main.py' is triggered.

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from src.notification import send_email

CHECK_INTERVAL_SECONDS = 60

def main():
	script_dir = Path(__file__).resolve().parent
	last_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

	while True:
		time.sleep(CHECK_INTERVAL_SECONDS)  # Check the time every 60 seconds.
		current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
		if current_hour != last_hour: # When a new hour is reached 'main.py' is run.
			last_hour = current_hour
			if current_hour.weekday() == 0 and current_hour.hour == 9:
				send_email() # Send portfolio update via email @ 9:00am every Monday
			subprocess.Popen(
				[sys.executable, str(script_dir / "main.py")], # Invoke main.py here
				cwd=script_dir,
			)

	
	
if __name__ == "__main__":
	main()
