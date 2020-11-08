import subprocess
import shlex


def set_system_time(time):
    subprocess.call(shlex.split("timedatectl set-ntp false"))
    subprocess.call(shlex.split(f"sudo date -s '{time}'"))

# https://stackoverflow.com/questions/12081310/python-module-to-change-system-date-and-time
