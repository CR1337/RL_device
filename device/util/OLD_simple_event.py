import time
from threading import Lock


class SimpleEventError(Exception):
    pass


class ChildEventIsNone(SimpleEventError):
    pass


class SimpleEvent():

    def __init__(self, sender=None, class_object=None):
        self._handlers = list()
        self._event_lock = Lock()
        self._counter_lock = Lock()
        self._call_lock = Lock()
        self._waiting_counter = 0
        self._sender = sender
        self._class_object = class_object
        self._event_lock.acquire()

        self._flag = False
        self._kwargs = dict()

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self

    def wait_for(self, timeout=None):
        t0 = time.time()

        if self._counter_lock.acquire(
            blocking=True,
            timeout=timeout if timeout is not None else -1
        ):
            self._waiting_counter += 1
            self._counter_lock.release()
        else:
            return False

        if timeout is not None:
            t1 = time.time()
            timeout -= t1 - t0
            if timeout <= 0:
                return False

        if self._event_lock.acquire(
            blocking=True,
            timeout=timeout if timeout is not None else -1
        ):
            self._event_lock.release()
        else:
            return False

        if timeout is not None:
            t2 = time.time()
            timeout -= t2 - t1
            if timeout <= 0:
                return False

        if self._counter_lock.acquire(
            blocking=True,
            timeout=timeout if timeout is not None else -1
        ):
            self._waiting_counter -= 1
            self._counter_lock.release()
        else:
            return False

        return True

    def __call__(self, **kwargs):
        self._call_lock.acquire(blocking=True)
        self._event_lock.release()

        self._flag = True
        self._kwargs = kwargs

        for handler in self._handlers:
            try:
                if isinstance(handler, (classmethod, staticmethod)):
                    handler.__func__(
                        self._class_object,
                        self._sender,
                        **kwargs
                    )
                else:
                    handler(self._sender, **kwargs)
            except ChildEventIsNone:
                self -= handler

        self._counter_lock.acquire(blocking=True)
        if self._waiting_counter == 0:
            self._event_lock.acquire(blocking=True)
        self._counter_lock.release()
        self._call_lock.release()

    def __lshift__(self, child_event):
        def event_wrapper(sender, kwargs):
            if child_event is None:
                raise ChildEventIsNone()
            if 'sender_list' in kwargs:
                kwargs['sender_list'].append(sender)
            else:
                kwargs['sender_list'] = [sender]
            child_event(**kwargs)
        self += event_wrapper

    def reset(self):
        self._call_lock.acquire(blocking=True)
        self._flag = False
        self._kwargs = dict()
        self._counter_lock.release()

    @property
    def subscription_count(self):
        return len(self._handlers)

    @property
    def waiting_count(self):
        return self._waiting_counter

    @property
    def sender(self):
        return self._sender

    @property
    def flag(self):
        return self._flag

    @property
    def kwargs(self):
        return self._kwargs
