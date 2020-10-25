import time
from datetime import datetime
from queue import Queue
from threading import Thread

import requests

from .config import Config


class MasterCommunicatorError(Exception):
    pass


class NotRegistered(MasterCommunicatorError):
    pass


class MasterCommunicator():

    _notification_thread = Thread()
    _heartbeat_thread = Thread()
    _notification_queue = Queue()
    _current_notification_data = None

    _master_registered = False
    _notification_url = None
    _master_address = None
    _master_port = None

    _stop_notification_flag = False
    _stop_heartbeat_flag = False

    @classmethod
    def register_master(cls, address, port):
        cls._master_address = address
        cls._master_port = port
        cls._notification_url = (
            f"http://{cls._master_address}:"
            f"{cls._master_port}/master/notification"
        )
        cls._heartbeat_url = (
            f"http://{cls._master_address}:"
            f"{cls._master_port}/master/heartbeat"
        )

        if not cls._notification_thread.is_alive():
            cls._notification_thread = Thread(
                target=cls._notification_handler,
                name="notification_handler"
            )
            cls._notification_thread.start()
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
        cls._notification_url = None
        cls._master_address = None
        cls._stop_notification = True
        cls._stop_heartbeat = True
        cls._master_port = None

    @classmethod
    def notify_run_scheduled_program(cls):
        cls._notify(
            data={
                'type': 'run_scheduled_program',
                'time': str(datetime.now())
            }
        )

    @classmethod
    def notify_fired(cls, raw_address):
        cls._notify(
            data={
                'type': 'fired',
                'fire_time': str(datetime.now()),
                'address': raw_address
            }
        )

    @classmethod
    def notify_program_finished(cls):
        cls._notify(
            data={
                'type': 'program_finished',
                'time': str(datetime.now())
            }
        )

    debug_notify_flag = False

    @classmethod
    def _notify(cls, data):
        if cls.debug_notify_flag:
            return
        else:
            cls.debug_notify_flag = True
            data['device_id'] = Config.get("connection", 'device_id')
            if not cls._master_registered:
                # raise NotRegistered()  # TODO: reacivate
                ...
            cls._notification_queue.put(data)

    @classmethod
    def _notification_handler(cls):
        counters = {
            'timeout': 0,
            'http_error': 0,
            'connection_error': 0,
            'request_exception': 0
        }

        while not cls._stop_notification_flag:
            if cls._current_notification_data is None:
                cls._current_notification_data = \
                    cls._notification_queue.get(block=True)
            success = False

            while not cls._stop_notification_flag:
                try:
                    response = requests.post(
                        url=cls._notification_url,
                        json=cls._current_notification_data,
                        timeout=Config.get('timeouts', 'notification')
                    )
                    response.raise_for_status()
                    for key in counters.keys():
                        if counters[key] > 0:
                            counters[key] = 0
                            ...  # TODO

                except requests.Timeout:
                    if counters['timeout'] == 0:
                        ...  # TODO
                    counters['timeout'] += 1

                except requests.HTTPError:
                    if counters['http_error'] == 0:
                        ...  # TODO
                    counters['http_error'] += 1

                except requests.ConnectionError:
                    if counters['connection_error'] == 0:
                        ...  # TODO
                    counters['connection_error'] += 1

                except requests.RequestException:
                    if counters['request_exception'] == 0:
                        ...  # TODO
                    counters['request_exception'] += 1

                else:
                    success = True

                finally:
                    if not success:
                        time.sleep(Config.get('timings', 'notification_sleep'))

        cls._stop_notification_flag = False

    @classmethod
    def _heartbeat_handler(cls):
        counters = {
            'timeout': 0,
            'http_error': 0,
            'connection_error': 0,
            'request_exception': 0
        }

        while not cls._stop_heartbeat_flag:
            try:
                # response = requests.post(
                #     url=cls._heartbeat_url,
                #     json={
                #         'type': 'heartbeat',
                #         'time': str(datetime.now()),
                #         'device_id': Environment.get('DEVICE_ID')
                #     },
                #     timeout=Config.get('timeouts', 'notification')
                # )
                # response.raise_for_status()
                # for key in counters.keys():
                #     if counters[key] > 0:
                #         counters[key] = 0
                #         logger.info(
                #             f"Success in _heartbeat_handler after "
                #             + f"{counters[key]} times {key}."
                #         )
                ...

            except requests.Timeout:
                if counters['timeout'] == 0:
                    ...  # TODO
                counters['timeout'] += 1

            except requests.HTTPError:
                if counters['http_error'] == 0:
                    ...  # TODO
                counters['http_error'] += 1

            except requests.ConnectionError:
                if counters['connection_error'] == 0:
                    ...  # TODO
                counters['connection_error'] += 1

            except requests.RequestException:
                if counters['request_exception'] == 0:
                    ...  # TODO
                counters['request_exception'] += 1

            time.sleep(Config.get('timings', 'heartbeat_period'))

        cls._stop_heartbeat_flag = False
