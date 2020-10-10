class TimestampError(Exception):
    def __init__(self, hours, minutes, seconds, deciseconds):
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.deciseconds = deciseconds


class InvalidType(TimestampError, TypeError):
    def __init__(self, hours, minutes, seconds, deciseconds):
        TimestampError.__init__(self, hours, minutes, seconds, deciseconds)
        self.hours_type = type(hours)
        self.minutes_type = type(minutes)
        self.seconds_type = type(seconds)
        self.deciseconds_type = type()


class InvalidValue(TimestampError, ValueError):
    def __init__(self, hours, minutes, seconds, deciseconds):
        TimestampError.__init__(self, hours, minutes, seconds, deciseconds)


class Timestamp():

    def __init__(self, hours, minutes, seconds, deciseconds):
        try:
            self._hours = int(hours)
            self._minutes = int(minutes)
            self._seconds = int(seconds)
            self._deciseconds = int(deciseconds)
        except ValueError:
            raise InvalidType(hours, minutes, seconds, deciseconds)

        if (
            hours < 0
            or 59 < minutes < 0
            or 59 < seconds < 0
            or 9 < deciseconds < 0
        ):
            raise InvalidValue(hours, minutes, seconds, deciseconds)

        self._total_seconds = (
            (hours * 3600)
            + (minutes * 60)
            + (seconds)
            + (deciseconds / 10)
        )

    @classmethod
    def get_timestamp_components(cls, total_seconds):
        deciseconds = (total_seconds - int(total_seconds)) * 10
        total_seconds = int(total_seconds)

        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return hours, minutes, seconds, deciseconds

    @property
    def hours(self):
        return self._hours

    @property
    def minutes(self):
        return self._minutes

    @property
    def seconds(self):
        return self._seconds

    @property
    def deciseconds(self):
        return self._deciseconds

    @property
    def total_seconds(self):
        return self._total_seconds
