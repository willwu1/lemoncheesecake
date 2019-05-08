'''
Created on Jan 24, 2016

@author: nicolas
'''

import os.path
from contextlib import contextmanager
import shutil
import threading
import traceback

import six

from lemoncheesecake.exceptions import LemonCheesecakeInternalError
from lemoncheesecake.consts import ATTACHEMENT_DIR, \
    LOG_LEVEL_DEBUG, LOG_LEVEL_ERROR, LOG_LEVEL_INFO, LOG_LEVEL_WARN
from lemoncheesecake.reporting import *
from lemoncheesecake import events
from lemoncheesecake.exceptions import ProgrammingError
from lemoncheesecake.fixtures import ScheduledFixtures


_runtime = None  # type: _Runtime

_scheduled_fixtures = None  # type: ScheduledFixtures


def initialize_runtime(event_manager, report_dir, report):
    global _runtime
    _runtime = _Runtime(event_manager, report_dir, report)
    event_manager.add_listener(_runtime)


def initialize_fixtures_cache(scheduled_fixtures):
    global _scheduled_fixtures
    _scheduled_fixtures = scheduled_fixtures


class _Runtime(object):
    def __init__(self, event_manager, report_dir, report):
        self.event_manager = event_manager
        self.report_dir = report_dir
        self.report = report
        self.attachments_dir = os.path.join(self.report_dir, ATTACHEMENT_DIR)
        self.attachment_count = 0
        self._attachment_lock = threading.Lock()
        self._failures = set()
        self._local = threading.local()
        self._local.location = None
        self._local.step = None

    def set_location(self, location):
        self._local.location = location

    @property
    def location(self):
        return self._local.location

    def mark_location_as_failed(self, location):
        self._failures.add(location)

    def is_successful(self, location):
        return location not in self._failures

    def is_everything_successful(self):
        return len(self._failures) == 0

    def set_step(self, description, detached=False):
        self._local.step = description
        self.event_manager.fire(events.StepEvent(self._local.location, description, detached=detached))

    def end_step(self, step):
        self.event_manager.fire(events.StepEndEvent(self._local.location, step))

    def log(self, level, content):
        if level == LOG_LEVEL_ERROR:
            self.mark_location_as_failed(self.location)
        self.event_manager.fire(events.LogEvent(self._local.location, self._local.step, level, content))

    def log_check(self, description, outcome, details):
        if outcome is False:
            self.mark_location_as_failed(self.location)
        self.event_manager.fire(events.CheckEvent(self._local.location, self._local.step, description, outcome, details))

    def log_url(self, url, description):
        self.event_manager.fire(events.LogUrlEvent(self._local.location, self._local.step, url, description))

    @contextmanager
    def prepare_attachment(self, filename, description, as_image=False):
        with self._attachment_lock:
            attachment_filename = "%04d_%s" % (self.attachment_count + 1, filename)
            self.attachment_count += 1
            if not os.path.exists(self.attachments_dir):
                os.mkdir(self.attachments_dir)

        yield os.path.join(self.attachments_dir, attachment_filename)

        self.event_manager.fire(events.LogAttachmentEvent(
            self._local.location, self._local.step, "%s/%s" % (ATTACHEMENT_DIR, attachment_filename),
            description, as_image
        ))


def get_runtime():
    # type: () -> _Runtime
    if not _runtime:
        raise LemonCheesecakeInternalError("Runtime is not initialized")
    return _runtime


def get_report():
    # type: () -> Report
    report = get_runtime().report
    if not report:
        raise LemonCheesecakeInternalError("Report is not (yet) accessible")
    return report


def set_step(description, detached=False):
    """
    Set a new step.
    """
    get_runtime().set_step(description, detached=detached)


def end_step(step):
    """
    End a detached step.
    """
    get_runtime().end_step(step)


@contextmanager
def detached_step(description):
    set_step(description, detached=True)
    try:
        yield
    except Exception:
        # FIXME: use exception instead of last implicit stacktrace
        stacktrace = traceback.format_exc()
        if six.PY2:
            stacktrace = stacktrace.decode("utf-8", "replace")
        log_error("Caught unexpected exception while running test: " + stacktrace)
    end_step(description)


def log_debug(content):
    """
    Log a debug level message.
    """
    get_runtime().log(LOG_LEVEL_DEBUG, content)


def log_info(content):
    """
    Log a info level message.
    """
    get_runtime().log(LOG_LEVEL_INFO, content)


def log_warning(content):
    """
    Log a warning level message.
    """
    get_runtime().log(LOG_LEVEL_WARN, content)


log_warn = log_warning


def log_error(content):
    """
    Log an error level message.
    """
    get_runtime().log(LOG_LEVEL_ERROR, content)


def log_check(description, outcome, details=None):
    get_runtime().log_check(description, outcome, details)


def _prepare_attachment(filename, description=None, as_image=False):
    return get_runtime().prepare_attachment(filename, description or filename, as_image=as_image)


def prepare_attachment(filename, description=None):
    """
    Prepare a attachment using a pseudo filename and an optional description.
    The function returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return _prepare_attachment(filename, description)


def prepare_image_attachment(filename, description=None):
    """
    Prepare an image attachment using a pseudo filename and an optional description.
    The function returns the real filename on disk that will be used by the caller
    to write the attachment content.
    """
    return _prepare_attachment(filename, description, as_image=True)


def _save_attachment_file(filename, description=None, as_image=False):
    with _prepare_attachment(os.path.basename(filename), description, as_image=as_image) as report_attachment_path:
        shutil.copy(filename, report_attachment_path)


def save_attachment_file(filename, description=None):
    """
    Save an attachment using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    return _save_attachment_file(filename, description)


def save_image_file(filename, description=None):
    """
    Save an image using an existing file (identified by filename) and an optional
    description. The given file will be copied.
    """
    return _save_attachment_file(filename, description, as_image=True)


def _save_attachment_content(content, filename, description=None, as_image=False):
    if type(content) is six.text_type:
        opening_mode = "w"
        if six.PY2:
            content = content.encode("utf-8")
    else:
        opening_mode = "wb"

    with _prepare_attachment(filename, description, as_image=as_image) as path:
        with open(path, opening_mode) as fh:
            fh.write(content)


def save_attachment_content(content, filename, description=None):
    """
    Save a given content as attachment using pseudo filename and optional description.
    """
    return _save_attachment_content(content, filename, description, as_image=False)


def save_image_content(content, filename, description=None):
    """
    Save a given image content as attachment using pseudo filename and optional description.
    """
    return _save_attachment_content(content, filename, description, as_image=True)


def log_url(url, description=None):
    """
    Log an URL.
    """
    get_runtime().log_url(url, description or url)


def get_fixture(name):
    """
    Return the corresponding fixture value. Only fixtures whose scope is pre_run can be retrieved.
    """
    global _scheduled_fixtures

    if not _scheduled_fixtures:
        raise ProgrammingError("Fixture cache has not yet been initialized")

    if not _scheduled_fixtures.has_fixture(name):
        raise ProgrammingError("Fixture '%s' either does not exist or don't have a prerun_session scope" % name)

    try:
        return _scheduled_fixtures.get_fixture_result(name)
    except AssertionError as excp:
        raise ProgrammingError(str(excp))


def add_report_info(name, value):
    report = get_report()
    report.add_info(name, value)


def set_runtime_location(location):
    get_runtime().set_location(location)


def mark_location_as_failed(location):
    get_runtime().mark_location_as_failed(location)


def is_location_successful(location):
    return get_runtime().is_successful(location)


def is_everything_successful():
    return get_runtime().is_everything_successful()


class Thread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)
        self.location = get_runtime().location

    def run(self):
        set_runtime_location(self.location)
        return super(Thread, self).run()
