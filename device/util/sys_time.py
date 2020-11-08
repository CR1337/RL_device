import subprocess
import shlex
from datetime import datetime


def set_system_time(time):
    subprocess.call(shlex.split("timedatectl set-ntp false"))
    subprocess.call(shlex.split(f"sudo date -s '{time}'"))


def get_system_time():
    datetime.now().replace(tzinfo=None).isoformat()

# https://stackoverflow.com/questions/12081310/python-module-to-change-system-date-and-time
