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


# class InvalidType(ConfigError, TypeError):
#     def __init__(self, category, key, value):
#         self.category = category
#         self.key = key
#         self.value = value
#         self.value_type = type(value)


class NoConfigFile(ConfigError, OSError):
    def __init__(self, filename):
        self.filename = filename


# class KeyProtected(ConfigError, KeyError):
#     def __init__(self, category, key):
#         self.category = category
#         self.key = key


class Config():
    _CONFIG_FILENAME = "device/config/config.json"
    # _META_CONFIG_FILENAME = "device/config/meta_config.json"

    # _CONFIG_FILENAME = "device/config/config.json"
    # _META_CONFIG_FILENAME = "device/config/meta_config.json"

    try:
        with open(_CONFIG_FILENAME, 'r', encoding='utf-8') as file:
            _config_data = json.load(file)
    except OSError:
        raise NoConfigFile(_CONFIG_FILENAME)

    # try:
    #     with open(_META_CONFIG_FILENAME, 'r', encoding='utf-8') as file:
    #         _meta_config_data = json.load(file)
    # except OSError:
    #     raise NoConfigFile(_META_CONFIG_FILENAME)

    # @classmethod
    # def update_many(cls, entries):
    #     if not isinstance(entries, list):
    #         raise TypeError()

    #     for entry in entries:
    #         if not isinstance(entry, dict):
    #             raise TypeError

    #         cls.update(
    #             category=entry['category'],
    #             key=entry['key'],
    #             value=entry['value']
    #         )

    # @classmethod
    # def update(cls, category, key, value):
    #     if category not in cls._config_data:
    #         raise InvalidCategory(category)
    #     if key not in cls._config_data[category]:
    #         raise InvalidKey(category, key)

    #     if cls._meta_config_data[category][key]['protected']:
    #         raise KeyProtected(category, key)

    #     if not isinstance(
    #         value,
    #         type(cls._meta_config_data[category][key]['type'])
    #     ):
    #         raise InvalidType(category, key, value)

    #     cls._config_data[category][key] = value

    @classmethod
    def get(cls, category, key):
        if category not in cls._config_data:
            raise InvalidCategory(category)
        if key not in cls._config_data[category]:
            raise InvalidKey(category, key)

        return cls._config_data[category][key]

    # @classmethod
    # def get_category(cls, category):
    #     if category not in cls._config_data:
    #         raise InvalidCategory(category)

    #     return cls._config_data[category]

    # @classmethod
    # def get_all(cls):
    #     return cls._config_data
