from __future__ import print_function

from typing import Iterable

from lemoncheesecake.testtree import TreeLocation
from lemoncheesecake.reporting import Report, Step, TestResult, SuiteResult, Log, Attachment, Url, Check
from lemoncheesecake import events
from lemoncheesecake.events import BaseEventManager
from lemoncheesecake.exceptions import LemonCheesecakeInternalError


def _replay_step(location, step, eventmgr):
    # type: (TreeLocation, Step, BaseEventManager) -> None
    eventmgr.fire(events.StepEvent(location, step.description, event_time=step.start_time))
    for entry in step.entries:
        if isinstance(entry, Log):
            eventmgr.fire(
                events.LogEvent(
                    location, step.description, entry.level, entry.message, entry.time
                )
            )
        elif isinstance(entry, Attachment):
            eventmgr.fire(
                events.LogAttachmentEvent(
                    location, step.description, entry.filename, entry.description, entry.as_image, entry.time
                )
            )
        elif isinstance(entry, Url):
            eventmgr.fire(
                events.LogUrlEvent(
                    location, step.description, entry.url, entry.description, entry.time
                )
            )
        elif isinstance(entry, Check):
            eventmgr.fire(
                events.CheckEvent(
                    location, step.description, entry.description, entry.outcome, entry.details, entry.time
                )
            )
        else:
            raise LemonCheesecakeInternalError("Unknown step entry %s" % entry)


def _replay_steps_events(location, steps, eventmgr):
    # type: (TreeLocation, Iterable[Step], BaseEventManager) -> None
    for step in steps:
        _replay_step(location, step, eventmgr)


def _replay_test_events(test, eventmgr):
    # type: (TestResult, BaseEventManager) -> None
    if test.status in ("passed", "failed", None):  # None means "in progress"
        eventmgr.fire(events.TestStartEvent(test, test.start_time))
        _replay_steps_events(TreeLocation.in_test(test), test.steps, eventmgr)
        if test.end_time:
            eventmgr.fire(events.TestEndEvent(test, test.end_time))
    elif test.status == "skipped":
        eventmgr.fire(events.TestSkippedEvent(test, test.status_details, test.start_time))
    elif test.status == "disabled":
        eventmgr.fire(events.TestDisabledEvent(test, test.status_details, test.start_time))
    else:
        raise LemonCheesecakeInternalError("Unknown test status '%s'" % test.status)


def _replay_suite_events(suite, eventmgr):
    # type: (SuiteResult, BaseEventManager) -> None

    eventmgr.fire(events.SuiteStartEvent(suite, suite.start_time))

    if suite.suite_setup:
        eventmgr.fire(events.SuiteSetupStartEvent(suite, suite.suite_setup.start_time))
        _replay_steps_events(TreeLocation.in_suite_setup(suite), suite.suite_setup.steps, eventmgr)
        if suite.suite_setup.end_time:
            eventmgr.fire(events.SuiteSetupEndEvent(suite, suite.suite_setup.end_time))

    for test in suite.get_tests():
        _replay_test_events(test, eventmgr)

    for sub_suite in suite.get_suites():
        _replay_suite_events(sub_suite, eventmgr)

    if suite.suite_teardown:
        eventmgr.fire(events.SuiteTeardownStartEvent(suite, suite.suite_teardown.start_time))
        _replay_steps_events(TreeLocation.in_suite_teardown(suite), suite.suite_teardown.steps, eventmgr)
        if suite.suite_teardown.end_time:
            eventmgr.fire(events.SuiteTeardownEndEvent(suite, suite.suite_teardown.end_time))

    if suite.end_time:
        eventmgr.fire(events.SuiteEndEvent(suite, suite.end_time))


def replay_report_events(report, eventmgr):
    # type: (Report, BaseEventManager) -> None

    eventmgr.fire(events.TestSessionStartEvent(report, report.start_time))

    if report.test_session_setup:
        eventmgr.fire(events.TestSessionSetupStartEvent(report.test_session_setup.start_time))
        _replay_steps_events(TreeLocation.in_test_session_setup(), report.test_session_setup.steps, eventmgr)
        if report.test_session_setup.end_time:
            eventmgr.fire(events.TestSessionSetupEndEvent(report.test_session_setup.end_time))

    for suite in report.get_suites():
        _replay_suite_events(suite, eventmgr)

    if report.test_session_teardown:
        eventmgr.fire(events.TestSessionTeardownStartEvent(report.test_session_teardown.start_time))
        _replay_steps_events(TreeLocation.in_test_session_teardown(), report.test_session_teardown.steps, eventmgr)
        if report.test_session_teardown.end_time:
            eventmgr.fire(events.TestSessionTeardownEndEvent(report.test_session_teardown.end_time))

    if report.end_time:
        eventmgr.fire(events.TestSessionEndEvent(report, report.end_time))
