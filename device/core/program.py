import time
from datetime import datetime
from threading import Thread

import numpy as np

# from .master_communication import MasterCommunicator
from .address import Address
from .config import Config
from .fire_command import FireCommand
from .timestamp import Timestamp


class ProgramError(Exception):
    pass


class InvalidProgram(ProgramError, ValueError):
    pass


class HangingProgramThread(ProgramError, RuntimeError):
    pass


class ProgramNotRunning(ProgramError):
    pass


class ProgramNotPaused(ProgramError):
    pass


class ProgramFinalized(ProgramError):
    pass


class ProgramNotFinalized(ProgramError):
    pass


class Program():

    def __init__(self, program_name):
        self._command_list = list()
        self._thread = None

        self._name = program_name

        self._pause_flag = False
        self._continue_flag = False
        self._stop_flag = False

        self._finalized = False

    def add_command(self, command):
        if self._finalized:
            raise ProgramFinalized()
        self._command_list.append(command)

    def finalize(self):
        if self._finalized:
            raise ProgramFinalized()
        self._finalized = True

    def run(self):
        if not self._finalized:
            raise ProgramNotFinalized()
        self._thread = Thread(target=self._execution_handler)
        self._thread.name = "__program_execution_thread__"
        self._thread.start()

    def pause(self):
        if not self._finalized:
            raise ProgramNotFinalized()
        if not self._thread.is_alive():
            raise ProgramNotRunning()
        self._pause_flag = True

    def continue_(self):
        if not self._finalized:
            raise ProgramNotFinalized()
        if not self._thread.is_alive():
            raise ProgramNotRunning()
        if not self._pause_flag:
            raise ProgramNotPaused()
        self._continue_flag = True

    def stop(self):
        if not self._finalized:
            raise ProgramNotFinalized()
        if not self._thread.is_alive():
            raise ProgramNotRunning()
        self._stop_flag = True
        self._thread.join(
            timeout=Config.get('timeouts', 'program_thread')
        )
        self._stop_flag = False
        if self._thread.is_alive():
            raise HangingProgramThread()

    def _pause_handler(self):
        while not self._continue_flag:
            if self._stop_flag:
                self._pause_flag = False
                self._continue_flag = False
                return
            time.sleep(Config.get('timings', 'resolution'))
        self._continue_flag = False
        self._pause_flag = False

    def _execution_handler(self):
        start_time = datetime.now()
        pause_time = None
        command_idx = 0

        while not self._stop_flag:

            if self._pause_flag:
                pause_time = datetime.now()
                self._pause_handler()
                start_time += (datetime.now() - pause_time)

            time.sleep(Config.get('timings', 'resolution'))

            command = self._command_list[command_idx]
            timestamp = datetime.now() - start_time
            if command.timestamp.total_seconds <= timestamp.total_seconds():
                command.fire()
                command_idx += 1
                if command_idx >= len(self._command_list):
                    break

        # MasterCommunicator.notify_program_finished()

    @property
    def fuse_status(self):
        result = Program.empty_fuse_status()
        for command in self._command_list:
            letter = command.address.letter
            number = command.address.number
            range_ = command.address.range

            for r in range(range_):
                if command.fired:
                    result[letter][number + r] = 'fired'
                elif command.fireing:
                    result[letter][number + r] = 'fireing'
                else:
                    result[letter][number + r] = 'staged'
        return result

    @property
    def name(self):
        return self._name

    @classmethod
    def empty_fuse_status(cls):
        chips = Config.get('i2c', 'chip_addresses').keys()
        return {chip: (['none'] * 16) for chip in chips}

    @classmethod
    def from_command_list(cls, commands, program_name):
        if not isinstance(commands, list):
            raise InvalidProgram()

        program = Program(program_name)

        for raw_command in commands:
            try:
                device_id = raw_command['device_id'].lower()
                raw_address = raw_command['address'].lower()
                hours = raw_command['h']
                minutes = raw_command['m']
                seconds = raw_command['s']
                milliseconds = raw_command['ms']
                if 'name' in raw_command:
                    name = raw_command['name']
                else:
                    name = ""
                if ' description' in raw_command:
                    description = raw_command['description']
                else:
                    description = ""
            except KeyError:
                raise InvalidProgram()

            if device_id != Config.get("connection", 'device_id'):
                continue

            timestamp = Timestamp(
                hours=hours,
                minutes=minutes,
                seconds=seconds,
                deciseconds=milliseconds  # TODO!
            )

            command = FireCommand(
                address=Address(raw_address),
                timestamp=timestamp,
                name=name,
                description=description
            )

            program.add_command(command)

        program.finalize()
        return program

    @classmethod
    def testloop_program(cls):
        program = Program("__TESTLOOP__")

        address_list = Address.full_address_list()
        for address, timestamp in zip(
            address_list,
            [
                Timestamp(*timestamp_components)
                for timestamp_components in [
                    Timestamp.get_timestamp_components(total_seconds)
                    for total_seconds in np.arange(
                        0,
                        len(address_list) * Config.get(
                            'timings',
                            'testloop_period'
                        ),
                        Config.get('timings', 'testloop_period')
                    )
                ]
            ]
        ):
            command = FireCommand(address, timestamp)
            program.add_command(command)

        return program
