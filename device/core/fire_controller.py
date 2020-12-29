from datetime import datetime
from enum import Enum, unique
# from functools import wraps
from threading import Lock, Thread
from time import sleep
import dateutil.parser

from .address import Address
from .config import Config
from .fire_command import FireCommand
from .hardware_controller import HardwareController, HardwareLocked
from .program import Program
# from .master_communication import MasterCommunicator


class FireControllerError(Exception):
    pass


class NoProgramLoaded(FireControllerError):
    pass


class ProgramLoaded(FireControllerError):
    pass


class ProgramRunning(FireControllerError):
    pass


class ProgramPaused(FireControllerError):
    pass


class NoProgramRunning(FireControllerError):
    pass


class ProgramScheduled(FireControllerError):
    def __init__(self, schedule_time):
        self.schedule_time = schedule_time


class NoProgramScheduled(FireControllerError):
    pass


class HangingScheduleThread(FireControllerError, RuntimeError):
    def __init__(self, schedule_time):
        self.schedule_time = schedule_time


UNLOADED = 'unloaded'
LOADED = 'loaded'
RUNNING = 'running'
PAUSED = 'paused'
RUNNING_TL = 'running_testloop'
PAUSED_TL = 'paused_testloop'
SCHEDULED = 'scheduled'
RUNNING_STATES = [
    RUNNING,
    RUNNING_TL
]
PAUSED_STATES = [
    PAUSED,
    PAUSED_TL
]
RUNNING_PAUSED_STATES = \
    RUNNING_STATES + PAUSED_STATES
NOT_RUNNING_STATES = [
    LOADED,
    UNLOADED
]


def lock_interaction(func):
    def wrapper(*args, **kwargs):
        FireController._interaction_lock.acquire(blocking=True)
        try:
            if isinstance(func, (classmethod, staticmethod)):
                func.__func__(FireController, *args, **kwargs)
            else:
                func(*args, **kwargs)
        except Exception:
            FireController._interaction_lock.release()
            raise
        FireController._interaction_lock.release()
    return wrapper


def raise_on_lock(func):
    def wrapper(*args, **kwargs):
        if HardwareController.is_locked():
            raise HardwareLocked()
        else:
            func(*args, **kwargs)
    return wrapper


class FireController():
    _program_state = UNLOADED
    _interaction_lock = Lock()
    _program = None
    _testloop_program = None
    _schedule_thread = None
    _scheduled_time = None

    _unschedule_flag = False

    @classmethod
    def raise_on_state(
        cls, states, exception, *exception_args, **exception_kwargs
    ):
        if not isinstance(states, (list, tuple)):
            states = [states]
        if cls._program_state in states:
            raise exception(*exception_args, **exception_kwargs)

    @lock_interaction
    @classmethod
    def load_program(cls, commands, program_name):
        cls.raise_on_state(RUNNING_STATES, ProgramRunning)
        cls.raise_on_state(
            SCHEDULED, ProgramScheduled, cls._scheduled_time
        )
        cls.raise_on_state(LOADED, ProgramLoaded)

        cls._program = Program.from_command_list(commands, program_name)
        cls._program_state = LOADED

    @lock_interaction
    @classmethod
    def delete_program(cls):
        cls.raise_on_state(RUNNING_PAUSED_STATES, ProgramRunning)
        cls.raise_on_state(SCHEDULED,
                           ProgramScheduled, cls._scheduled_time)
        cls.raise_on_state(UNLOADED, NoProgramLoaded)

        cls._program = None
        cls._program_state = UNLOADED

    @raise_on_lock
    @lock_interaction
    @classmethod
    def run_program(cls):
        cls.raise_on_state(RUNNING_PAUSED_STATES, ProgramRunning)
        cls.raise_on_state(SCHEDULED,
                           ProgramScheduled, cls._scheduled_time)
        cls.raise_on_state(UNLOADED, NoProgramLoaded)

        cls._run_program()

    @lock_interaction
    @classmethod
    def pause_program(cls):
        cls.raise_on_state(NOT_RUNNING_STATES, NoProgramRunning)
        cls.raise_on_state(PAUSED_STATES, ProgramPaused)
        cls.raise_on_state(SCHEDULED,
                           ProgramScheduled, cls._scheduled_time)

        cls._program.pause()
        if cls._program_state is RUNNING_TL:
            cls._program_state = PAUSED_TL
        else:
            cls._program_state = PAUSED

    @raise_on_lock
    @lock_interaction
    @classmethod
    def continue_program(cls):
        cls.raise_on_state(NOT_RUNNING_STATES, NoProgramRunning)
        cls.raise_on_state(RUNNING_STATES, ProgramRunning)
        cls.raise_on_state(SCHEDULED,
                           ProgramScheduled, cls._scheduled_time)

        cls._program.continue_()
        if cls._program_state is PAUSED_TL:
            cls._program_state = RUNNING_TL
        else:
            cls._program_state = RUNNING

    @lock_interaction
    @classmethod
    def stop_program(cls):
        cls.raise_on_state(NOT_RUNNING_STATES, NoProgramRunning)
        cls.raise_on_state(SCHEDULED,
                           ProgramScheduled, cls._scheduled_time)

        cls._program.stop()
        cls._program_state = LOADED

    @raise_on_lock
    @lock_interaction
    @classmethod
    def schedule_program(cls, scheduled_time):
        cls.raise_on_state(RUNNING_STATES, ProgramRunning)
        cls.raise_on_state(SCHEDULED,
                           ProgramScheduled, cls._scheduled_time)
        cls.raise_on_state(UNLOADED, NoProgramLoaded)

        cls._schedule_thread = Thread(
            target=cls._schedule_handler,
            name='__SCHEDULE_THREAD__'
        )
        cls._scheduled_time = dateutil.parser.parse(
            scheduled_time
        ).replace(tzinfo=None)
        cls._schedule_thread.start()
        cls._program_state = SCHEDULED

    @lock_interaction
    @classmethod
    def unschedule_program(cls):
        cls.raise_on_state(RUNNING_STATES, ProgramRunning)
        cls.raise_on_state(NOT_RUNNING_STATES, NoProgramScheduled)

        cls._unschedule_flag = True
        cls._schedule_thread.join(
            timeout=Config.get('timeouts', 'schedule_thread')
        )
        if cls._schedule_thread.is_alive():
            raise HangingScheduleThread(cls._scheduled_time)
        cls._schedule_thread = None
        cls._program_state = LOADED

    @raise_on_lock
    @lock_interaction
    @classmethod
    def fire(cls, raw_address):
        cls.raise_on_state(RUNNING_STATES, ProgramRunning)
        cls.raise_on_state(LOADED, ProgramLoaded)
        cls.raise_on_state(SCHEDULED,
                           ProgramScheduled, cls._scheduled_time)

        address = Address(raw_address)
        command = FireCommand(address, None)
        command.fire()

    @raise_on_lock
    @lock_interaction
    @classmethod
    def testloop(cls):
        cls.raise_on_state(RUNNING_STATES, ProgramRunning)
        cls.raise_on_state(LOADED, ProgramLoaded)
        cls.raise_on_state(SCHEDULED,
                           ProgramScheduled, cls._scheduled_time)

        cls._testloop_program = Program.testloop_program()
        cls._testloop_program.run(
            callback=cls._testloop_execution_callback_factory()
        )
        cls._program_state = RUNNING_TL

    @classmethod
    def _run_program(cls):
        cls._program.run(
            callback=cls._program_execution_callback_factory()
        )
        cls._program_state = RUNNING

    @classmethod
    def _program_state_setter_factory(cls, program_state):
        def program_state_setter():
            cls._program_state = program_state
        return program_state_setter

    @classmethod
    def _program_execution_callback_factory(cls):
        state_setter = cls._program_state_setter_factory(UNLOADED)

        def program_execution_callback():
            state_setter()
            cls._program = None
            cls._testloop_program = None

        return program_execution_callback

    @classmethod
    def _testloop_execution_callback_factory(cls):
        state_setter = cls._program_state_setter_factory(cls._program_state)

        def testloop_execution_callback():
            state_setter()
            cls._testloop_program = None

        return testloop_execution_callback

    @classmethod
    def _schedule_handler(cls):
        while not cls._unschedule_flag:
            if datetime.now().replace(tzinfo=None) >= cls._scheduled_time:
                break
            try:
                sleep(Config.get('timings', 'resolution'))
            except Exception:
                ...  # TODO
        else:
            cls._unschedule_flag = False
            return
        try:
            cls._run_program()
        except Exception:
            ...  # TODO

    @classmethod
    def get_program_state(cls):
        return cls._program_state

    @classmethod
    def set_program_state(cls, program_state):
        cls._program_state = program_state

    @classmethod
    def get_fuse_status(cls):
        if cls._program is None and cls._testloop_program is None:
            return Program.empty_fuse_status()
        else:
            return cls._program.fuse_status

    @classmethod
    def get_scheduled_time(cls):
        return cls._scheduled_time

    @classmethod
    def get_program_name(cls):
        if cls._program is None:
            return None
        else:
            return cls._program.name
