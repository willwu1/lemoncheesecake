'''
Created on Mar 29, 2016

@author: nicolas
'''

import os
import os.path as osp

from lemoncheesecake.exceptions import InvalidReportFile, ProgrammingError, method_not_implemented
from lemoncheesecake.utils import object_has_method
from lemoncheesecake.reporting.report import Report
from lemoncheesecake import events

__all__ = (
    "get_available_backends", "ReportingBackend", "ReportingSession",
    "save_report", "load_reports_from_dir", "load_report",
    "filter_available_reporting_backends", "filter_reporting_backends_by_capabilities",
    "CAPABILITY_REPORTING_SESSION", "CAPABILITY_SAVE_REPORT", "CAPABILITY_LOAD_REPORT"
)

CAPABILITY_REPORTING_SESSION = 0x1
CAPABILITY_SAVE_REPORT = 0x2
CAPABILITY_LOAD_REPORT = 0x4

SAVE_AT_END_OF_TESTS = 1
SAVE_AT_EACH_SUITE = 2
SAVE_AT_EACH_TEST = 3
SAVE_AT_EACH_FAILED_TEST = 4
SAVE_AT_EACH_EVENT = 5


class ReportingSession:
    def begin_tests(self):
        pass

    def end_tests(self):
        pass

    def begin_test_session_setup(self):
        pass

    def end_test_session_setup(self, outcome):
        pass

    def begin_test_session_teardown(self):
        pass

    def end_test_session_teardown(self, outcome):
        pass

    def begin_suite(self, suite):
        pass

    def begin_suite_setup(self, suite):
        pass

    def end_suite_setup(self, suite, outcome):
        pass

    def begin_suite_teardown(self, suite):
        pass

    def end_suite_teardown(self, suite, outcome):
        pass

    def end_suite(self, suite):
        pass

    def begin_test(self, test):
        pass

    def end_test(self, test, status):
        pass

    def skip_test(self, test, reason):
        pass

    def disable_test(self, test):
        pass

    def set_step(self, description):
        pass

    def log(self, level, content):
        pass

    def check(self, description, outcome, details=None):
        pass


class ReportingBackend:
    def is_available(self):
        return True

    def get_capabilities(self):
        capabilities = 0
        if object_has_method(self, "create_reporting_session"):
            capabilities |= CAPABILITY_REPORTING_SESSION
        if object_has_method(self, "save_report"):
            capabilities |= CAPABILITY_SAVE_REPORT
        if object_has_method(self, "load_report"):
            capabilities |= CAPABILITY_LOAD_REPORT
        return capabilities

    def register_reporting_session(self, report_dir, report):
        session = self.create_reporting_session(report_dir, report)
        events.subscribe_to_event_types({
            "on_tests_beginning": session.begin_tests,
            "on_tests_ending": session.end_tests,

            "on_test_session_setup_beginning": session.begin_test_session_setup,
            "on_test_session_setup_ending": session.end_test_session_setup,
            "on_test_session_teardown_beginning": session.begin_test_session_teardown,
            "on_test_session_teardown_ending": session.end_test_session_teardown,

            "on_suite_beginning": session.begin_suite,
            "on_suite_ending": session.end_suite,
            "on_suite_setup_beginning": session.begin_suite_setup,
            "on_suite_setup_ending": session.end_suite_setup,
            "on_suite_teardown_beginning": session.begin_suite_teardown,
            "on_suite_teardown_ending": session.end_suite_teardown,

            "on_test_beginning": session.begin_test,
            "on_test_ending": session.end_test,
            "on_skipped_test": session.skip_test,
            "on_disabled_test": session.disable_test,

            "on_step": session.set_step,
            "on_log": session.log,
            "on_check": session.check
        })


#     def create_reporting_session(self, dir, report):
#         method_not_implemented("create_reporting_session", self)
#
#     def save_report(self, filename, report):
#         method_not_implemented("serialize_report", self)
#
#     def load_report(self, filename):
#         method_not_implemented("unserialize_report", self)


class FileReportSession(ReportingSession):
    def __init__(self, report_filename, report, save_func, save_mode):
        self.report_filename = report_filename
        self.report = report
        self.save_func = save_func
        self.save_mode = save_mode

    def save(self):
        self.save_func(self.report_filename, self.report)

    def _handle_code_end(self, is_failure):
        if (self.save_mode == SAVE_AT_EACH_TEST) or (self.save_mode == SAVE_AT_EACH_FAILED_TEST and is_failure):
            self.save()
            return

    def end_test_session_setup(self, outcome):
        self._handle_code_end(
            self.report.test_session_setup.has_failure() if self.report.test_session_setup else False
        )

    def end_test_session_teardown(self, outcome):
        self._handle_code_end(
            self.report.test_session_teardown.has_failure() if self.report.test_session_teardown else False
        )

    def end_suite_setup(self, suite, outcome):
        self._handle_code_end(outcome is False)

    def end_suite_teardown(self, suite, outcome):
        self._handle_code_end(outcome is False)

    def end_test(self, test, status):
        self._handle_code_end(test)

    def end_suite(self, suite):
        if self.save_mode == SAVE_AT_EACH_SUITE:
            self.save()

    def log(self, level, content):
        if self.save_mode == SAVE_AT_EACH_EVENT:
            self.save()

    def check(self, description, outcome, details=None):
        if self.save_mode == SAVE_AT_EACH_EVENT:
            self.save()

    def end_tests(self):
        self.save()


class FileReportBackend(ReportingBackend):
    def __init__(self, save_mode=SAVE_AT_EACH_FAILED_TEST):
        self.save_mode = save_mode

    def get_report_filename(self):
        method_not_implemented("get_report_filename", self)

    def create_reporting_session(self, report_dir, report):
        return FileReportSession(
            os.path.join(report_dir, self.get_report_filename()), report, self.save_report, self.save_mode
        )


def filter_available_reporting_backends(backends):
    return list(filter(lambda backend: backend.is_available(), backends))


def filter_reporting_backends_by_capabilities(backends, capabilities):
    return list(filter(lambda backend: backend.get_capabilities() & capabilities == capabilities, backends))


def get_available_backends():
    from lemoncheesecake.reporting.backends import ConsoleBackend, XmlBackend, JsonBackend, HtmlBackend, JunitBackend

    return list(filter(lambda b: b.is_available(), [ConsoleBackend(), XmlBackend(), JsonBackend(), HtmlBackend(), JunitBackend()]))


class BoundReport(Report):
    def __init__(self):
        Report.__init__(self)
        self.backend = None
        self.path = None

    def bind(self, backend, path):
        self.backend = backend
        self.path = path
        return self

    def is_bound(self):
        return self.backend is not None and self.path is not None

    def save(self):
        if not self.is_bound():
            raise ProgrammingError("Cannot save unbound report")
        save_report(self.path, self, self.backend)


def load_report_from_file(filename, backends=None):
    if backends is None:
        backends = get_available_backends()
    for backend in backends:
        if backend.get_capabilities() & CAPABILITY_LOAD_REPORT:
            try:
                return backend.load_report(filename)
            except IOError as excp:
                raise InvalidReportFile("Cannot load report from file '%s': %s" % (filename, excp))
            except InvalidReportFile:
                pass
    raise InvalidReportFile("Cannot find any suitable report backend to unserialize file '%s'" % filename)


def load_reports_from_dir(dirname, backends=None):
    for filename in [os.path.join(dirname, filename) for filename in os.listdir(dirname)]:
        if os.path.isfile(filename):
            try:
                yield load_report_from_file(filename, backends)
            except InvalidReportFile:
                pass


def load_report(path, backends=None):
    if osp.isdir(path):
        try:
            return next(load_reports_from_dir(path, backends))
        except StopIteration:
            raise InvalidReportFile("Cannot find any report in directory '%s'" % path)
    else:
        return load_report_from_file(path, backends)


def save_report(filename, report, backend):
    if not backend.get_capabilities() & CAPABILITY_SAVE_REPORT:
        raise ProgrammingError("Reporting backend '%s' does not support save operation" % backend.name)
    backend.save_report(filename, report)