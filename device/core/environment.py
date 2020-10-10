import json
import os


class EnvorinmentError(Exception):
    pass


class NoEnvironmentFile(EnvorinmentError, OSError):
    def __init__(self, filename):
        self.filename = filename


class InvalidKey(EnvorinmentError, KeyError):
    def __init__(self, key):
        self.key = key


class Environment():
    _ENVIRONMENT_FILENAME = "device/config/environment.json"

    # _ENVIRONMENT_FILENAME = "device/config/environment.json"

    try:
        with open(_ENVIRONMENT_FILENAME, 'r', encoding='utf-8') as file:
            _environment_keys = json.load(file)
    except OSError:
        raise NoEnvironmentFile(_ENVIRONMENT_FILENAME)

    @classmethod
    def get(cls, key):
        # # FIXME: for debugging only:
        # if key == "DEVICE_ID":
        #     return "sat1"
        # if key == "EXTERNAL_PORT":
        #     return 5000
        # if key == "INTERNAL_PORT":
        #     return 5000
        # #

        if key in cls._environment_keys and key in os.environ:
            return os.environ[key]
        else:
            raise InvalidKey(key)

    @classmethod
    def get_all(cls):
        return {
            key: cls.get(key)
            for key in cls._environment_keys
        }
