import time
from threading import Thread

from .config import Config
from .hardware_controller import HardwareController


class FireCommandError(Exception):
    def __init__(self, address):
        self.raw_address = address.raw_address


class HangingFireThread(FireCommandError, RuntimeError):
    def __init__(self, address):
        FireCommandError.__init__(self, address)


class CommandNotFired(FireCommandError):
    def __init__(self, address):
        FireCommandError.__init__(self, address)


class AlreadyFired(FireCommandError):
    def __init__(self, address):
        FireCommandError.__init__(self, address)


class AlreadyJoined(FireCommandError):
    def __init__(self, address):
        FireCommandError.__init__(self, address)


class FireCommand():

    def __init__(self, address, timestamp=None, name=None, description=None):
        self._address = address
        self._timestamp = timestamp
        self._name = name
        self._description = description
        self._thread = Thread(target=self._fire_handler)
        self._thread.name = f"__fire_thread_{self._address}__"
        self._fired = False
        self._fireing = False

    def _fire_handler(self):
        self._fireing = True

        try:
            HardwareController.light(self._address)
        except Exception:
            ... # TODO

        try:
            time.sleep(Config.get('timings', 'ignition'))
        except Exception:
            ... # TODO

        try:
            HardwareController.unlight(self._address)
        except Exception:
            ... # TODO

        self._fireing, self._fired = False, True

    def fire(self):
        if self._fired or self._fireing:
            raise AlreadyFired(self._address)
        self._thread.start()

    @property
    def address(self):
        return self._address

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def fired(self):
        return self._fired

    @property
    def fireing(self):
        return self._fireing
