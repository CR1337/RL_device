import time
from threading import Thread

import requests

from .config import Config
from ..util.sys_time import get_system_time
from .hardware_controller import HardwareController
from .fire_controller import FireController


class MasterCommunicatorError(Exception):
    pass


class NotRegistered(MasterCommunicatorError):
    pass


class MasterCommunicator():

    _heartbeat_thread = Thread()

    _master_registered = False
    _master_address = None
    _master_port = None

    _stop_heartbeat_flag = False

    @classmethod
    def register_master(cls, address, port):
        cls._master_address = address
        cls._master_port = port
        cls._heartbeat_url = (
            f"http://{cls._master_address}:"
            f"{cls._master_port}/master/heartbeat"
        )

        if not cls._heartbeat_thread.is_alive():
            cls._heartbeat_thread = Thread(
                target=cls._heartbeat_handler,
                name="heartbeat_handler"
            )
            cls._heartbeat_thread.start()
        cls._master_registered = True

    @classmethod
    def deregister_master(cls):
        if not cls._master_registered:
            raise NotRegistered()
        cls._master_registered = False
        cls._master_address = None
        cls._stop_heartbeat_flag = True
        cls._master_port = None

    @classmethod
    def _heartbeat_handler(cls):
        while not cls._stop_heartbeat_flag:
            try:
                response = requests.post(
                    url=cls._heartbeat_url,
                    json={
                        'device_id': Config.get('connection', 'device_id'),
                        'system_time': get_system_time(),
                        'locked': HardwareController.is_locked(),
                        'program_state': FireController.get_program_state(),
                        'scheduled_time': FireController.get_scheduled_time(),
                        'program_name': FireController.get_program_name(),
                        'fuse_states': FireController.get_fuse_status(),
                        'error_states': HardwareController.errors()
                    },
                    timeout=Config.get('timeouts', 'notification')
                )
                response.raise_for_status()

            except requests.RequestException:
                print(cls._heartbeat_url)
                print("requests.RequestException!")
                ...  # TODO

            time.sleep(Config.get('timings', 'heartbeat_period'))

        cls._stop_heartbeat_flag = False
