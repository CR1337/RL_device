import re
from itertools import product

from .config import Config


class AddressError(Exception):
    def __init__(self, raw_adress):
        self.raw_address = raw_adress


class AddressSyntaxError(AddressError, SyntaxError):
    def __init__(self, raw_address):
        AddressError.__init__(self, raw_address)


class InvalidAddress(AddressError, ValueError):
    def __init__(self, raw_address):
        AddressError.__init__(self, raw_address)


class InvalidChip(InvalidAddress, ValueError):
    def __init__(self, raw_address):
        InvalidAddress.__init__(self, raw_address)


class InvalidFuse(InvalidAddress, ValueError):
    def __init__(self, raw_address):
        InvalidAddress.__init__(self, raw_address)


class InvalidRange(InvalidAddress, ValueError):
    def __init__(self, raw_address):
        InvalidAddress.__init__(self, raw_address)


class Address():

    REGISTER_ADDRESSES = {
        'lock': 0x00,
        'error_control': 0x01,
        'fuse': [0x14, 0x15, 0x16, 0x17],
        'error': [0x1d, 0x1e]
    }

    MASKS = {
        'lock': 0x10,
        'error_control': 0x80
    }

    REV_MASKS = {
        key: 0xff - value
        for key, value in MASKS.items()
    }

    ADDRESS_TUPLE_RANGE = product(
        Config.get('i2c', 'chip_addresses').values(),
        [0x00, 0x01, 0x14, 0x15, 0x16, 0x17, 0x1d, 0x1e]  # TODO: as function of REGISTER_ADDRESSES
    )

    _REGEX_STRINGS = {
        'syntax': (
            r"[A-Za-z](([048]|12(:[1-4])?)|([159]|13(:[1-3])?)"
            + r"|([26]|(1[04])(:[1-2])?)|([37]|(1[15])(:1)?))"
        ),
        'letter': r"(?P<letter>[A-Za-z])",
        'number': r"([A-Za-z])(?P<number>[0-9]|(1[0-5]))(:|$)",
        'range': r"(:)(?P<range>[1-4])"
    }

    _REGEX_MODULES = {
        key: re.compile(value)
        for key, value in _REGEX_STRINGS.items()
    }

    def __init__(self, raw_address):
        self._raw_address = raw_address

        # self._validate_syntax()

        self._letter = None
        self._number = None
        self._range = None
        self._extract_components()
        self._validate_components()

        self._chip_address = None
        self._read_chip_address()

        self._fuse_address = None
        self._error_address = None
        self._calc_register_addresses()

        self._fuse_mask = 0x00
        self._error_mask = 0x00
        self._calc_register_masks()

    def _validate_syntax(self):
        if not Address._REGEX_MODULES['syntax'].fullmatch(self._raw_address):
            raise AddressSyntaxError(self._raw_address)

    def _extract_components(self):
        letter_match = Address._REGEX_MODULES['letter'].search(
            self._raw_address)
        number_match = Address._REGEX_MODULES['number'].search(
            self._raw_address)
        range_match = Address._REGEX_MODULES['range'].search(
            self._raw_address)

        if letter_match is None or number_match is None:
            raise AddressSyntaxError(self._raw_address)

        self._letter = letter_match.group('letter').lower()
        self._number = int(number_match.group('number'))
        self._range = 1 if range_match is None \
            else int(range_match.group('range'))

    def _validate_components(self):
        if not any([
            (self._letter in [chip.lower(), chip.upper()])
            for chip in Config.get('i2c', 'chip_addresses').keys()
        ]):
            raise InvalidChip(self._raw_address)

        if self._number not in range(0, 16):
            raise InvalidFuse(self._raw_address)

        if self._range > 4 - (self._number % 4):
            raise InvalidRange(self._raw_address)

    def _read_chip_address(self):
        self._chip_address = Config.get('i2c', 'chip_addresses')[self._letter]

    def _calc_register_addresses(self):
        self._fuse_address = Address.REGISTER_ADDRESSES['fuse'][
            self._number // 4
        ]
        self._error_address = Address.REGISTER_ADDRESSES['error'][
            self._number // 8
        ]

    def _calc_register_masks(self):
        for idx in range(self._range):
            self._fuse_mask += 1 << (((self._number + idx) % 4) * 2)

    def __repr__(self):
        return self.raw_address

    @property
    def raw_address(self):
        return f"{self._letter}{self._number}:{self._range}"

    @property
    def chip_address(self):
        return self._chip_address

    @property
    def register_address(self):
        return self._fuse_address

    @property
    def error_register_address(self):
        return self._error_address

    @property
    def register_mask(self):
        return self._fuse_mask

    @property
    def rev_register_mask(self):
        return 0xff - self._fuse_mask

    @property
    def address_tuple(self):
        return (
            self._chip_address,
            self._fuse_address
        )

    @property
    def letter(self):
        return self._letter

    @property
    def number(self):
        return self._number

    @property
    def range(self):
        return self._range

    @classmethod
    def full_address_list(self):
        return [
            Address(letter + str(number))
            for letter, number in product(
                Config.get('i2c', 'chip_addresses').keys(),
                range(16)
            )
        ]
