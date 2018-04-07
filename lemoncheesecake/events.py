import time
import re
import inspect

from lemoncheesecake.utils import camel_case_to_snake_case


def _get_event_name_from_class_name(class_name):
    return re.sub("_event$", "", camel_case_to_snake_case(class_name))


class Event(object):
    def __init__(self):
        self.time = time.time()

    @classmethod
    def get_name(cls):
        return _get_event_name_from_class_name(cls.__name__)


class EventType:
    def __init__(self, event_class):
        self._event_class = event_class
        self._handlers = []

    def subscribe(self, handler):
        self._handlers.append(handler)

    def unsubscribe(self, handler):
        self._handlers.remove(handler)

    def reset(self):
        self._handlers = []

    def fire(self, event):
        for handler in self._handlers:
            handler(event)


def _get_event_name(val):
    return val.get_name() if inspect.isclass(val) and issubclass(val, Event) else val


class EventManager:
    def __init__(self):
        self._event_types = {}

    def register_events(self, *event_classes):
        for event_class in event_classes:
            self._event_types[event_class.get_name()] = EventType(event_class)

    def reset(self, event_name=None):
        if event_name is None:
            for event_type in self._event_types.values():
                event_type.reset()
        else:
            self._event_types[event_name].reset()

    def subscribe_to_event(self, event, handler):
        self._event_types[_get_event_name(event)].subscribe(handler)

    def subscribe_to_events(self, event_handler_pairs):
        for event, handler in event_handler_pairs.items():
            self.subscribe_to_event(event, handler)

    def add_listener(self, listener):
        for event_name in self._event_types:
            handler_name = "on_%s" % event_name
            handler = getattr(listener, handler_name, None)
            if handler and callable(handler):
                self.subscribe_to_event(event_name, handler)

    def unsubscribe_from_event(self, event, handler):
        self._event_types[_get_event_name(event)].unsubscribe(handler)

    def fire(self, event):
        self._event_types[event.__class__.get_name()].fire(event)


eventmgr = EventManager()
register_event = eventmgr.register_events
register_events = eventmgr.register_events
subscribe_to_event = eventmgr.subscribe_to_event
subscribe_to_events = eventmgr.subscribe_to_events
unsubscribe_from_event = eventmgr.unsubscribe_from_event
add_listener = eventmgr.add_listener
reset = eventmgr.reset
fire = eventmgr.fire


def event(class_):
    register_event(class_)
    return class_


###
# Events related to the test session
###

class _ReportEvent(Event):
    def __init__(self, report):
        super(_ReportEvent, self).__init__()
        self.report = report


@event
class TestSessionStartEvent(_ReportEvent):
    pass


@event
class TestSessionEndEvent(_ReportEvent):
    pass


@event
class TestSessionSetupStartEvent(Event):
    pass


@event
class TestSessionSetupEndEvent(Event):
    pass


@event
class TestSessionTeardownStartEvent(Event):
    pass


@event
class TestSessionTeardownEndEvent(Event):
    pass


###
# Suite events
###

class _SuiteEvent(Event):
    def __init__(self, suite):
        super(_SuiteEvent, self).__init__()
        self.suite = suite


@event
class SuiteStartEvent(_SuiteEvent):
    pass


@event
class SuiteEndEvent(_SuiteEvent):
    pass


@event
class SuiteSetupStartEvent(_SuiteEvent):
    pass


@event
class SuiteSetupEndEvent(_SuiteEvent):
    pass


@event
class SuiteTeardownStartEvent(_SuiteEvent):
    pass


@event
class SuiteTeardownEndEvent(_SuiteEvent):
    pass


###
# Test events
###

class _TestEvent(Event):
    def __init__(self, test):
        super(_TestEvent, self).__init__()
        self.test = test


@event
class TestStartEvent(_TestEvent):
    pass


@event
class TestEndEvent(_TestEvent):
    pass


@event
class TestSkippedEvent(_TestEvent):
    def __init__(self, test, reason):
        super(TestSkippedEvent, self).__init__(test)
        self.skipped_reason = reason


@event
class TestDisabledEvent(_TestEvent):
    def __init__(self, test, reason):
        super(TestDisabledEvent, self).__init__(test)
        self.disabled_reason = reason


@event
class TestSetupStartEvent(_TestEvent):
    pass


@event
class TestSetupEndEvent(_TestEvent):
    def __init__(self, test, outcome):
        super(TestSetupEndEvent, self).__init__(test)
        self.setup_outcome = outcome


@event
class TestTeardownStartEvent(_TestEvent):
    pass


@event
class TestTeardownEndEvent(_TestEvent):
    def __init__(self, test, outcome):
        super(TestTeardownEndEvent, self).__init__(test)
        self.teardown_outcome = outcome


###
# Transverse test execution events
###

class RuntimeEvent(Event):
    def __init__(self, location):
        super(RuntimeEvent, self).__init__()
        self.location = location


@event
class StepEvent(RuntimeEvent):
    def __init__(self, location, description):
        super(StepEvent, self).__init__(location)
        self.step_description = description


class SteppedEvent(RuntimeEvent):
    def __init__(self, location, step):
        super(SteppedEvent, self).__init__(location)
        self.step = step


@event
class LogEvent(SteppedEvent):
    def __init__(self, location, step, level, message):
        super(LogEvent, self).__init__(location, step)
        self.log_level = level
        self.log_message = message


@event
class CheckEvent(SteppedEvent):
    def __init__(self, location, step, description, outcome, details=None):
        super(CheckEvent, self).__init__(location, step)
        self.check_description = description
        self.check_outcome = outcome
        self.check_details = details


@event
class LogAttachmentEvent(SteppedEvent):
    def __init__(self, location, step, path, filename, description):
        super(LogAttachmentEvent, self).__init__(location, step)
        self.attachment_path = path
        self.attachment_filename = filename
        self.attachment_description = description


@event
class LogUrlEvent(SteppedEvent):
    def __init__(self, location, step, url, description):
        super(LogUrlEvent, self).__init__(location, step)
        self.url = url
        self.url_description = description
