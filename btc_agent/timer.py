# This script is constantly running. It checks the time every 60 seconds. When the time passes onto a new hour, 'main.py' is triggered.

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CHECK_INTERVAL_SECONDS = 60

def main():
	script_dir = Path(__file__).resolve().parent
	last_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

	while True:
		time.sleep(CHECK_INTERVAL_SECONDS)  # Check the time every 60 seconds.
		current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
		if current_hour != last_hour:
			last_hour = current_hour
			subprocess.Popen(
				[sys.executable, str(script_dir / "main.py")], # Invoke main.py here
				cwd=script_dir,
			)


if __name__ == "__main__":
	main()
