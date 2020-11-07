import subprocess
import shlex
from _datetime import datetime


def set_system_time(
    year=2020,
    month=12,
    day=31,
    hour=0,
    minute=0,
    second=0,
    millisecond=0
):
    try:
        time_string = datetime(
            year, month, day,
            hour, minute, second, millisecond
        ).isoformat()
        subprocess.call(shlex.split("timedatectl set-ntp false"))
        subprocess.call(shlex.split(f"sudo date -s '{time_string}'"))
        subprocess.call(shlex.split("sudo hwclock -w"))
    except Exception:
        print("Could not change system time!")

# https://stackoverflow.com/questions/12081310/python-module-to-change-system-date-and-time
