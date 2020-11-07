import json
from itertools import product
from threading import Lock
import os

from .address import Address
from .config import Config


if not os.path.exists("/dev/i2c-1"):
    print("HARDWARE IS SIMULATED!")

    class SMBus():

        def __init__(self, bus_address):
            self._data_filename = "device/simulation/simulation_data.json"

        def write_byte_data(self, i2c_address, reg_address, value):
            print("Write:", i2c_address, reg_address, value)
            with open(
                self._data_filename, 'r', encoding='utf-8'
            ) as file:
                simulation_data = json.load(file)
            simulation_data[str(i2c_address)][reg_address] = value
            with open(
                self._data_filename, 'w', encoding='utf-8'
            ) as file:
                json.dump(simulation_data, file)

        def read_byte_data(self, i2c_address, reg_address):
            with open(
                self._data_filename, 'r', encoding='utf-8'
            ) as file:
                simulation_data = json.load(file)
            value = simulation_data[str(i2c_address)][reg_address]
            print("Read:", i2c_address, reg_address, value)
            return value
else:
    from smbus2 import SMBus


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


class HardwareController():

    LOCKS = {
        address_tuple: Lock()
        for address_tuple in Address.ADDRESS_TUPLE_RANGE
    }
    ERROR_CONTROL_LOCKS = {
        chip_address: Lock()
        for chip_address in Config.get('i2c', 'chip_addresses').keys()
    }
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
    def light(cls, address):
        cls.LOCKS[address.address_tuple].acquire(blocking=True)
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
        cls.LOCKS[address.address_tuple].release()

    @classmethod
    def unlight(cls, address):
        cls.LOCKS[address.address_tuple].acquire(blocking=True)
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
        cls.LOCKS[address.address_tuple].release()

    @classmethod
    def unlight_all(cls):
        for chip_address, register_address in product(
            Config.get('i2c', 'chip_addresses').items(),
            Address.REGISTER_ADDRESSES['fuse']
        ):
            cls._write(chip_address, register_address, 0x00)

    @classmethod
    def lock(cls):
        for chip_address in Config.get('i2c', 'chip_addresses').values():
            cls._write(
                chip_address,
                Address.REGISTER_ADDRESSES['lock'],
                Address.MASKS['lock']
            )

    @classmethod
    def unlock(cls):
        for chip_address in Config.get('i2c', 'chip_addresses').values():
            cls._write(
                chip_address,
                Address.REGISTER_ADDRESSES['lock'],
                Address.MASKS['unlock']
            )

    @classmethod
    def clear_error_flags(cls):
        for chip_address in Config.get('i2c', 'chip_addresses').keys():
            cls.ERROR_CONTROL_LOCKS[chip_address].acquire(blocking=True)
            value = cls._read(
                chip_address,
                Address.REGISTER_ADDRESSES['error_control']
            )
            value |= Address.MASKS['error_control']
            cls._write(
                chip_address,
                Address.REGISTER_ADDRESSES['error_control'],
                value
            )
            value &= Address.REV_MASKS['error_control']
            cls._write(
                chip_address,
                Address.REGISTER_ADDRESSES['error_control'],
                value
            )
            cls.ERROR_CONTROL_LOCKS[chip_address].release()

    @classmethod
    def is_locked(cls):
        for chip_addr in Config.get('i2c', 'chip_addresses').values():
            value = cls._read(chip_addr, Address.REGISTER_ADDRESSES['lock'])
            value &= Address.MASKS['lock']
            if value > 0:
                return True
        return False

    @classmethod
    def errors(cls):
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
