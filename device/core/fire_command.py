import time
from threading import Thread

from .config import Config
from .logger import Logger
from .hardware_controller import HardwareController
from .address import Address


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
        logger = Logger(logger_type='auto')
        self._fireing = True

        try:
            HardwareController.light(self._address)
        except Exception:
            logger.exception(f"Exception when lighting {self._address}.")

        try:
            time.sleep(Config.get('timings', 'ignition'))
        except Exception:
            logger.exception(
                f"Exception while waiting for unlighting {self._address}."
            )

        try:
            HardwareController.unlight(self._address)
        except Exception:
            logger.exception(
                f"Exception when unlighting {self._address}."
            )

        self._fireing, self._fired = False, True

    def fire(self):
        if self._fired or self._fireing:
            raise AlreadyFired(self._address)
        self._thread.start()

    # def join(self, timeout=None):
    #     try:
    #         self._thread.join(timeout=timeout)
    #     except RuntimeError:
    #         raise AlreadyJoined(self._address)
    #     else:
    #         if not self._fired or self._fireing:
    #             raise CommandNotFired(self._address)
    #     if self._thread.is_alive():
    #         raise HangingFireThread(self._address)

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
