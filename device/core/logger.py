import io
import logging
import os
import zipfile
from logging.handlers import RotatingFileHandler

from ..util.simple_event import SimpleEvent
from .config import Config


class LoggingError(Exception):
    pass


class NoLogDirectory(LoggingError, OSError):
    def __init__(self, directory):
        self.directory = directory


class InvalidLoggerType(LoggingError):
    def __init__(self, logger_type):
        self.logger_type = logger_type


class InvalidLogFile(LoggingError, OSError):
    def __init__(self, logfile_name):
        self.logfile_name = logfile_name


class Logger():
    _LOG_DIRECTORY = "device/logs"
    # _LOG_DIRECTORY = "device/logs"
    if not os.path.exists(_LOG_DIRECTORY):
        raise NoLogDirectory(_LOG_DIRECTORY)
    _LOG_FILENAME = ".".join([
        Config.get("connection", 'device_id'),
        "log"
    ])
    _full_log_filename = os.path.join(_LOG_DIRECTORY, _LOG_FILENAME)
    _logging_level = logging.DEBUG

    _formatter = logging.Formatter()  # TODO

    _handler = RotatingFileHandler(
        filename=_full_log_filename,
        encoding='utf-8',
        backupCount=Config.get('logs', 'max_log_files')
    )
    _handler.setLevel(_logging_level)
    _handler.setFormatter(_formatter)

    _rest_logger = logging.getLogger("REST_logger")
    _rest_logger.setLevel(_logging_level)
    _rest_logger.addHandler(_handler)

    _auto_logger = logging.getLogger("AUTO_logger")
    _auto_logger.setLevel(_logging_level)
    _auto_logger.addHandler(_handler)

    _instance_counter = 0

    log_event = SimpleEvent()

    @classmethod
    def _log(cls, log_func, message, *args, **kwargs):
        log_func(message, *args, **kwargs)
        cls.log_event(
            sender=cls,
            log_func=log_func,
            message=message,
            args=args,
            kwargs=kwargs
        )

    @classmethod
    def get_logfiles(cls, amount):
        logfile_names = cls._get_archived_logfile_names()
        amount = min(int(amount), Config.get('logs', 'max_log_files'))
        logfile_names = logfile_names[0:amount - 1]
        logfile_names = (
            [os.path.join(cls._LOG_DIRECTORY, cls._LOG_FILENAME)]
            + logfile_names
        )

        mem_file = io.BytesIO()
        with zipfile.ZipFile(mem_file, 'w') as zip_file:
            for filename in logfile_names:
                zip_file.write(filename, os.path.basename(filename))
        mem_file.seek(0)
        return mem_file

    @classmethod
    def _get_archived_logfile_names(cls):
        result = list()
        for filename in os.listdir(cls._LOG_DIRECTORY):
            if not filename.startswith(cls._LOG_FILENAME):
                continue
            if filename == cls._LOG_FILENAME:
                continue
            file_path = os.path.join(cls._LOG_DIRECTORY, filename)
            try:
                if os.path.isfile(file_path):
                    result.append(file_path)
            except OSError:
                raise InvalidLogFile(file_path)
        return sorted(result, reverse=True)

    def __init__(self, logger_type):
        if logger_type == 'rest':
            self._logger = Logger._rest_logger
        elif logger_type == 'auto':
            self._logger = Logger._auto_logger
        else:
            raise InvalidLoggerType(logger_type)

    def debug(self, message, *args, **kwargs):
        Logger._log(self._logger.debug, message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        Logger._log(self._logger.info, message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        Logger._log(self._logger.warning, message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        Logger._log(self._logger.error, message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        Logger._log(self._logger.ciritcal, message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        Logger._log(self._logger.exception, message, *args, **kwargs)
