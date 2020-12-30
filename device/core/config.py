import json


class ConfigError(Exception):
    pass


class InvalidCategory(ConfigError, KeyError):
    def __init__(self, category):
        self.category = category


class InvalidKey(ConfigError, KeyError):
    def __init__(self, category, key):
        self.category = category
        self.key = key


class NoConfigFile(ConfigError, OSError):
    def __init__(self, filename):
        self.filename = filename


class Config():
    _CONFIG_FILENAME = "device/config/config.json"

    try:
        with open(_CONFIG_FILENAME, 'r', encoding='utf-8') as file:
            _config_data = json.load(file)
    except OSError:
        raise NoConfigFile(_CONFIG_FILENAME)

    @classmethod
    def get(cls, category, key):
        if category not in cls._config_data:
            raise InvalidCategory(category)
        if key not in cls._config_data[category]:
            raise InvalidKey(category, key)

        return cls._config_data[category][key]
