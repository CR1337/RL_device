from functools import wraps
from itertools import product
from threading import Lock

from smbus2 import SMBus

from .address import Address
from .config import Config


class HardwareError(Exception):
    pass


class HardwareLocked(HardwareError):
    pass


class ReadError(HardwareError, OSError):
    def __init__(self, bus_address, i2c_address, register_address):
        self.bus_address = bus_address
        self.i2c_address = i2c_address
        self.register_address = register_address


class WriteError(HardwareError, OSError):
    def __init__(self, bus_address, i2c_address, register_address, value):
        self.bus_address = bus_address
        self.i2c_address = i2c_address
        self.register_address = register_address
        self.value = value


class InvalidBusType(TypeError):
    def __init__(self, bus_address):
        self.bus_address = bus_address


class BusError(HardwareError, OSError):
    def __init__(self, bus_address):
        self.bus_address = bus_address


def lock_bus(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        HardwareController.LOCK.acquire(blocking=True)
        result = func(*args, **kwargs)
        HardwareController.LOCK.release()
        return result
    return wrapper


class HardwareController():

    LOCK = Lock()

    try:
        BUS = SMBus(Config.get('i2c', 'bus_address'))
    except TypeError:
        raise InvalidBusType(Config.get('i2c', 'bus_address'))
    except OSError:
        raise BusError(Config.get('i2c', 'bus_address'))

    @classmethod
    def _write(cls, i2c_address, register_address, value):
        try:
            cls.BUS.write_byte_data(i2c_address, register_address, value)
            print(f"WRITE {value} TO {i2c_address}:{register_address}")
        except OSError:
            raise WriteError(
                Config.get('i2c', 'bus_address'),
                i2c_address,
                register_address,
                value
            )

    @classmethod
    def _read(cls, i2c_address, register_address):
        try:
            value = cls.BUS.read_byte_data(i2c_address, register_address)
            return value
        except OSError:
            raise ReadError(
                Config.get('i2c', 'bus_address'),
                i2c_address,
                register_address
            )

    @classmethod
    @lock_bus
    def light(cls, address):
        value = cls._read(
            address.chip_address,
            address.register_address
        )
        value &= address.rev_register_mask
        value |= address.register_mask
        cls._write(
            address.chip_address,
            address.register_address,
            value
        )

    @classmethod
    @lock_bus
    def unlight(cls, address):
        value = cls._read(
            address.chip_address,
            address.register_address
        )
        value &= address.rev_register_mask
        cls._write(
            address.chip_address,
            address.register_address,
            value
        )

    @classmethod
    @lock_bus
    def lock(cls):
        for chip_address in Config.get('i2c', 'chip_addresses').values():
            cls._write(
                chip_address,
                Address.REGISTER_ADDRESSES['lock'],
                Address.MASKS['lock']
            )

    @classmethod
    @lock_bus
    def unlock(cls):
        for chip_address in Config.get('i2c', 'chip_addresses').values():
            cls._write(
                chip_address,
                Address.REGISTER_ADDRESSES['lock'],
                Address.MASKS['unlock']
            )

    @classmethod
    @lock_bus
    def is_locked(cls):
        for chip_addr in Config.get('i2c', 'chip_addresses').values():
            value = cls._read(chip_addr, Address.REGISTER_ADDRESSES['lock'])
            value &= Address.MASKS['lock']
            if value > 0:
                return True
        return False

    @classmethod
    @lock_bus
    def errors(cls):
        # maybe generates false errors?
        return {
            chip_letter: [
                False if (value & mask) == 0 else True
                for value, mask in product(
                    [
                        cls._read(chip_address, reg_address)
                        for reg_address in Address.REGISTER_ADDRESSES['error']
                    ],
                    range(8)  # 8 bools per register
                )
            ]
            for chip_letter, chip_address
            in Config.get('i2c', 'chip_addresses').items()
        }
