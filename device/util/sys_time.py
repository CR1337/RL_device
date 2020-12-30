import shlex
import subprocess
from datetime import datetime


def set_system_time(time):
    subprocess.call(shlex.split("timedatectl set-ntp false"))
    subprocess.call(shlex.split(f"sudo date -s '{time}'"))


def get_system_time():
    return datetime.now().replace(tzinfo=None).isoformat()
