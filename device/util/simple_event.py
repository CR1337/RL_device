from threading import Lock
import types
import itertools
import random


class SimpleEventError(Exception):
    pass


class NoClassObjectError(SimpleEventError):
    pass


class NoSimpleEventInstance(SimpleEventError):
    pass


class NoClassInstanceError(SimpleEventError):
    pass


class HandlerNotCallable(SimpleEventError):
    pass


class NoSuchHandler(SimpleEventError):
    pass


class SimpleEvent():

    class EventHandler():

        def __init__(self, func, cls_object=None, self_object=None):
            self._func = func
            self._cls_object = cls_object
            self._self_object = self_object

        def __call__(self, sender, **kwargs):
            # if isinstance(self._func, classmethod):
            #     if 'sender' in self._func.__code__.co_varnames:
            #         self._func.__call__(self._cls_object, sender, **kwargs)
            #     else:
            #         self._func.__call__(self._cls_object, **kwargs)
            # elif isinstance(self._func, types.MethodType):
            #     if 'sender' in self._func.__code__.co_varnames:
            #         self._func.__call__(self._self_object, sender, **kwargs)
            #     else:
            #         self._func.__call__(self._self_object, **kwargs)
            # else:
            #     if 'sender' in self._func.__code__.co_varnames:
            #         self._func.__call__(sender, **kwargs)
            #     else:
            #         self._func.__call__(**kwargs)

            if 'sender' in self._func.__code__.co_varnames:
                kwargs['sender'] = sender
            self._func.__call__(**kwargs)

    def __init__(self):
        self._handlers = dict()
        self._flag = False
        self._kwargs = dict()
        self._handler_ids = self._handler_id_generator()
        self._hash = random.randint(0, 2 ** 64 - 1)

        self._call_lock = Lock()

    def __hash__(self):
        return self._hash

    def _add_handler(self, handler):
        handler_id = next(self._handler_ids)
        with self._call_lock:
            self._handlers[handler_id] = handler
        return handler_id

    def _handler_id_generator(self):
        for i in itertools.count(start=0):
            yield hash(self) + i

    def add_classmethod_handler(self, handler, cls_object):
        if not isinstance(handler, types.MethodType):
            raise NoClassObjectError
        handler = SimpleEvent.EventHandler(handler, cls_object=cls_object)
        return self._add_handler(handler)

    def add_method_handler(self, handler, self_object):
        if not isinstance(handler, types.MethodType):
            raise NoClassInstanceError
        handler = SimpleEvent.EventHandler(handler, self_object=self_object)
        return self._add_handler(handler)

    def add_simpleevent_handler(self, handler):
        if not isinstance(handler, SimpleEvent):
            raise NoSimpleEventInstance
        handler = SimpleEvent.EventHandler(
            handler, self_object=handler
        )
        return self._add_handler(handler)

    def add_handler(self, handler):
        if not callable(handler):
            raise HandlerNotCallable
        handler = SimpleEvent.EventHandler(handler)
        return self._add_handler(handler)

    def remove_handler(self, handler_id):
        if handler_id in self._handlers.keys():
            with self._call_lock:
                del self._handlers[handler_id]
        else:
            raise NoSuchHandler

    def __call__(self, sender, **kwargs):
        with self._call_lock:
            self._flag = True
            self._kwargs = kwargs
            for handler in self._handlers.values():
                handler(sender=sender, **kwargs)

    def reset(self):
        with self._call_lock:
            self._flag = False
            self._kwargs = dict()

    @property
    def subscription_count(self):
        return len(self._handlers)

    @property
    def sender(self):
        return self._sender

    @property
    def flag(self):
        return self._flag

    @property
    def kwargs(self):
        return self._kwargs
