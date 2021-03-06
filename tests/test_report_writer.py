 # -*- coding: utf-8 -*-

'''
Created on Nov 1, 2016

@author: nicolas
'''

import os.path as osp
import time

import six

import lemoncheesecake.api as lcc

from helpers.runner import run_suite_class, run_suite_classes, run_func_in_test
from helpers.report import assert_report_from_suite, assert_report_from_suites, get_last_test, get_last_attachment, \
    assert_attachment

SAMPLE_IMAGE_PATH = osp.join(osp.dirname(__file__), osp.pardir, "doc", "_static", "report-sample.png")

with open(SAMPLE_IMAGE_PATH, "rb") as fh:
    SAMPLE_IMAGE_CONTENT = fh.read()


def _get_suite(report, suite_path=None):
    return report.get_suite(suite_path) if suite_path else report.get_suites()[0]


def _get_suite_setup(report, suite_path=None):
    suite = _get_suite(report, suite_path)
    return suite.suite_setup


def _get_suite_teardown(report, suite_path=None):
    suite = _get_suite(report, suite_path)
    return suite.suite_teardown


def make_file_reader(encoding=None, binary=False):
    def reader(path):
        with open(path, "rb" if binary else "r") as fh:
            content = fh.read()
        if encoding and six.PY2:
            content = content.decode(encoding)
        return content
    return reader


def test_simple_test():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    assert_report_from_suite(report, mysuite)


def test_test_with_all_metadata():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.link("http://foo.bar", "foobar")
        @lcc.prop("foo", "bar")
        @lcc.tags("foo", "bar")
        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    assert_report_from_suite(report, mysuite)


def test_suite_with_all_metadata():
    @lcc.link("http://foo.bar", "foobar")
    @lcc.prop("foo", "bar")
    @lcc.tags("foo", "bar")
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    assert_report_from_suite(report, mysuite)


def test_multiple_suites_and_tests():
    @lcc.suite("MySuite1")
    class mysuite1:
        @lcc.tags("foo")
        @lcc.test("Some test 1")
        def test_1_1(self):
            pass

        @lcc.tags("bar")
        @lcc.test("Some test 2")
        def test_1_2(self):
            pass

        @lcc.tags("baz")
        @lcc.test("Some test 3")
        def test_1_3(self):
            pass

    @lcc.suite("MySuite2")
    class mysuite2:
        @lcc.prop("foo", "bar")
        @lcc.test("Some test 1")
        def test_2_1(self):
            pass

        @lcc.prop("foo", "baz")
        @lcc.test("Some test 2")
        def test_2_2(self):
            pass

        @lcc.test("Some test 3")
        def test_2_3(self):
            pass

        # suite3 is a sub suite of suite2
        @lcc.suite("MySuite3")
        class mysuite3:
            @lcc.prop("foo", "bar")
            @lcc.test("Some test 1")
            def test_3_1(self):
                pass

            @lcc.prop("foo", "baz")
            @lcc.test("Some test 2")
            def test_3_2(self):
                pass

            @lcc.test("Some test 3")
            def test_3_3(self):
                pass

    report = run_suite_classes([mysuite1, mysuite2])

    assert_report_from_suites(report, [mysuite1, mysuite2])


def test_check_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_that("somevalue", "foo", lcc.equal_to("foo"))

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "foo" in step.entries[0].description
    assert step.entries[0].outcome is True
    assert "foo" in step.entries[0].details


def test_check_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.check_that("somevalue", "foo", lcc.equal_to("bar"))

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "failed"
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "bar" in step.entries[0].description
    assert step.entries[0].outcome is False
    assert "foo" in step.entries[0].details


def test_require_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.require_that("somevalue", "foo", lcc.equal_to("foo"))

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "foo" in step.entries[0].description
    assert step.entries[0].outcome is True
    assert "foo" in step.entries[0].details


def test_require_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.require_that("somevalue", "foo", lcc.equal_to("bar"))

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "failed"
    step = test.steps[0]
    assert "somevalue" in step.entries[0].description
    assert "bar" in step.entries[0].description
    assert step.entries[0].outcome is False
    assert "foo" in step.entries[0].details


def test_all_types_of_logs():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Test 1")
        def test_1(self):
            lcc.log_debug("some debug message")
            lcc.log_info("some info message")
            lcc.log_warn("some warning message")

        @lcc.test("Test 2")
        def test_2(self):
            lcc.log_error("some error message")

    report = run_suite_class(mysuite)

    test = report.get_test("mysuite.test_1")
    assert test.status == "passed"
    step = test.steps[0]
    assert step.entries[0].level == "debug"
    assert step.entries[0].message == "some debug message"
    assert step.entries[1].level == "info"
    assert step.entries[1].message == "some info message"
    assert step.entries[2].level == "warn"

    test = report.get_test("mysuite.test_2")
    assert test.status == "failed"
    step = test.steps[0]
    assert step.entries[0].message == "some error message"
    assert step.entries[0].level == "error"


def test_multiple_steps():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step 1")
            lcc.log_info("do something")
            lcc.set_step("step 2")
            lcc.log_info("do something else")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    assert test.steps[0].description == "step 1"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "do something"
    assert test.steps[1].description == "step 2"
    assert test.steps[1].entries[0].level == "info"
    assert test.steps[1].entries[0].message == "do something else"


def test_concurrent_steps():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step 1", detached=True)
            lcc.set_step("step 2", detached=True)
            lcc.log_info("do something else", step="step 2")
            lcc.log_info("do something", step="step 1")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    assert test.steps[0].description == "step 1"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "do something"
    assert test.steps[1].description == "step 2"
    assert test.steps[1].entries[0].level == "info"
    assert test.steps[1].entries[0].message == "do something else"


def test_multiple_steps_on_different_threads():
    def thread_func(i):
        lcc.set_step(str(i), detached=True)
        time.sleep(0.001)
        lcc.log_info(str(i))
        lcc.end_step(str(i))

    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            threads = [lcc.Thread(target=thread_func, args=(i,)) for i in range(3)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    remainings = list(range(3))

    for step in test.steps:
        remainings.remove(int(step.description))
        assert len(step.entries) == 1
        assert step.entries[0].message == step.description

    assert len(remainings) == 0


def test_exception_in_thread_detached_step():
    def thread_func():
        with lcc.detached_step("step"):
            lcc.log_info("doing something")
            raise Exception("this_is_an_exception")

    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            thread = lcc.Thread(target=thread_func)
            thread.start()
            thread.join()

    report = run_suite_class(mysuite)

    test = get_last_test(report)

    assert test.status == "failed"
    assert test.steps[0].description == "step"
    assert test.steps[0].entries[-1].level == "error"
    assert "this_is_an_exception" in test.steps[0].entries[-1].message


def test_end_step_on_detached_step():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.set_step("step", detached=True)
            lcc.log_info("log")
            lcc.end_step("step")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    assert test.steps[0].description == "step"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "log"


def test_detached_step():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            with lcc.detached_step("step"):
                lcc.log_info("log")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    assert test.steps[0].description == "step"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "log"


def test_default_step():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.log_info("do something")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    assert test.steps[0].description == "Some test"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "do something"


def test_step_after_test_setup():
    @lcc.suite("mysuite")
    class mysuite:
        def setup_test(self, test):
            lcc.log_info("in test setup")

        @lcc.test("Some test")
        def sometest(self):
            lcc.log_info("do something")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.status == "passed"
    assert test.steps[0].description == "Setup test"
    assert test.steps[0].entries[0].level == "info"
    assert test.steps[0].entries[0].message == "in test setup"
    assert test.steps[1].description == "Some test"
    assert test.steps[1].entries[0].level == "info"
    assert test.steps[1].entries[0].message == "do something"


def test_prepare_attachment(tmpdir):
    def do():
        with lcc.prepare_attachment("foobar.txt", "some description") as filename:
            with open(filename, "w") as fh:
                fh.write("some content")

    report = run_func_in_test(do, tmpdir=tmpdir)

    assert_attachment(
        get_last_attachment(report), "foobar.txt", "some description", False, "some content", make_file_reader()
    )


def test_prepare_image_attachment(tmpdir):
    def do():
        with lcc.prepare_image_attachment("foobar.png", "some description") as filename:
            with open(filename, "wb") as fh:
                fh.write(SAMPLE_IMAGE_CONTENT)

    report = run_func_in_test(do, tmpdir=tmpdir)

    assert_attachment(
        get_last_attachment(report), "foobar.png", "some description", True, SAMPLE_IMAGE_CONTENT,
        make_file_reader(binary=True)
    )


def test_save_attachment_file(tmpdir):
    def do():
        filename = osp.join(tmpdir.strpath, "somefile.txt")
        with open(filename, "w") as fh:
            fh.write("some other content")
        lcc.save_attachment_file(filename, "some other file")

    report = run_func_in_test(do, tmpdir=tmpdir.mkdir("report"))

    assert_attachment(
        get_last_attachment(report), "somefile.txt", "some other file", False, "some other content", make_file_reader()
    )


def test_save_image_file(tmpdir):
    def do():
        lcc.save_image_file(SAMPLE_IMAGE_PATH, "some other file")

    report = run_func_in_test(do, tmpdir=tmpdir.mkdir("report"))

    assert_attachment(
        get_last_attachment(report), osp.basename(SAMPLE_IMAGE_PATH), "some other file", True, SAMPLE_IMAGE_CONTENT,
        make_file_reader(binary=True)
    )


def _test_save_attachment_content(tmpdir, file_name, file_content, binary_mode, file_reader):
    def do():
        lcc.save_attachment_content(file_content, file_name, binary_mode=binary_mode)

    report = run_func_in_test(do, tmpdir=tmpdir)

    assert_attachment(get_last_attachment(report), file_name, file_name, False, file_content, file_reader)


def test_save_attachment_text_ascii(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.txt", "foobar", False, make_file_reader())


def test_save_attachment_text_utf8(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.txt", u"éééçççààà", False, make_file_reader(encoding="utf-8"))


def test_save_attachment_binary(tmpdir):
    _test_save_attachment_content(tmpdir, "foobar.png", SAMPLE_IMAGE_CONTENT, True, make_file_reader(binary=True))


def test_save_image_content(tmpdir):
    def do():
        lcc.save_image_content(SAMPLE_IMAGE_CONTENT, "somefile.png", "some file")

    report = run_func_in_test(do, tmpdir=tmpdir)

    assert_attachment(
        get_last_attachment(report), "somefile.png", "some file", True, SAMPLE_IMAGE_CONTENT,
        make_file_reader(binary=True)
    )


def test_log_url():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.log_url("http://example.com", "example")

    report = run_suite_class(mysuite)

    test = get_last_test(report)
    assert test.steps[0].entries[0].description == "example"
    assert test.steps[0].entries[0].url == "http://example.com"


def test_unicode(tmpdir):
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("some test")
        def sometest(self):
            lcc.set_step(u"éééààà")
            lcc.check_that(u"éééààà", 1, lcc.equal_to(1))
            lcc.log_info(u"éééààà")
            lcc.save_attachment_content("A" * 1024, u"somefileààà", u"éééààà")

    report = run_suite_class(mysuite, tmpdir=tmpdir)

    test = get_last_test(report)
    assert test.status == "passed"
    step = test.steps[0]
    assert step.description == u"éééààà"
    assert u"éééààà" in step.entries[0].description
    assert "1" in step.entries[0].description
    assert step.entries[1].message == u"éééààà"
    assert_attachment(step.entries[2], u"somefileààà", u"éééààà", False, "A" * 1024, make_file_reader(encoding="utf8"))


def test_setup_suite_success():
    @lcc.suite("MySuite")
    class mysuite:
        def setup_suite(self):
            lcc.log_info("some log")

        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    setup = _get_suite_setup(report)
    assert setup.outcome is True
    assert setup.start_time is not None
    assert setup.end_time is not None
    assert setup.steps[0].entries[0].message == "some log"
    assert setup.is_successful()


def test_setup_suite_failure():
    @lcc.suite("MySuite")
    class mysuite:
        def setup_suite(self):
            lcc.log_error("something bad happened")

        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    setup = _get_suite_setup(report)
    assert setup.outcome is False
    assert setup.start_time is not None
    assert setup.end_time is not None
    assert setup.steps[0].entries[0].message == "something bad happened"
    assert not setup.is_successful()


def test_setup_suite_without_content():
    @lcc.suite("MySuite")
    class mysuite:
        def setup_suite(self):
            pass

        @lcc.test("Some test")
        def sometest(self):
            pass

    report = run_suite_class(mysuite)

    assert _get_suite_setup(report) is None


def test_teardown_suite_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.log_info("some log")

    report = run_suite_class(mysuite)

    teardown = _get_suite_teardown(report)
    assert teardown.outcome is True
    assert teardown.start_time is not None
    assert teardown.end_time is not None
    assert teardown.steps[0].entries[0].message == "some log"
    assert teardown.is_successful()


def test_teardown_suite_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            lcc.check_that("val", 1, lcc.equal_to(2))

    report = run_suite_class(mysuite)

    teardown = _get_suite_teardown(report)
    assert teardown.outcome is False
    assert teardown.start_time is not None
    assert teardown.end_time is not None
    assert teardown.steps[0].entries[0].outcome is False
    assert not teardown.is_successful()


def test_teardown_suite_without_content():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            pass

        def teardown_suite(self):
            pass

    report = run_suite_class(mysuite)

    assert _get_suite_teardown(report) is None


def test_setup_test_session_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_info("some log")

    report = run_suite_class(mysuite, fixtures=[fixt])

    setup = report.test_session_setup
    assert setup.outcome is True
    assert setup.start_time is not None
    assert setup.end_time is not None
    assert setup.steps[0].entries[0].message == "some log"
    assert setup.is_successful()


def test_setup_test_session_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        lcc.log_error("something bad happened")

    report = run_suite_class(mysuite, fixtures=[fixt])

    setup = report.test_session_setup
    assert setup.outcome is False
    assert setup.start_time is not None
    assert setup.end_time is not None
    assert setup.steps[0].entries[0].message == "something bad happened"
    assert not setup.is_successful()


def test_setup_test_session_without_content():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        pass

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert report.test_session_setup is None


def test_teardown_test_session_success():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        yield
        lcc.log_info("some log")

    report = run_suite_class(mysuite, fixtures=[fixt])

    teardown = report.test_session_teardown
    assert teardown.outcome is True
    assert teardown.start_time is not None
    assert teardown.end_time is not None
    assert teardown.steps[0].entries[0].message == "some log"
    assert teardown.is_successful()


def test_teardown_test_session_failure():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        yield
        lcc.check_that("val", 1, lcc.equal_to(2))

    report = run_suite_class(mysuite, fixtures=[fixt])

    teardown = report.test_session_teardown
    assert teardown.outcome is False
    assert teardown.start_time is not None
    assert teardown.end_time is not None
    assert teardown.steps[0].entries[0].outcome is False
    assert not teardown.is_successful()


def test_teardown_test_session_without_content():
    @lcc.suite("MySuite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self, fixt):
            pass

    @lcc.fixture(scope="session")
    def fixt():
        yield

    report = run_suite_class(mysuite, fixtures=[fixt])

    assert report.test_session_teardown is None


def test_add_report_info():
    @lcc.suite("Some suite")
    class mysuite:
        @lcc.test("Some test")
        def sometest(self):
            lcc.add_report_info("some info", "some data")

    report = run_suite_class(mysuite)

    assert report.info[-1] == ["some info", "some data"]
