import time

import pytest

from lemoncheesecake.reporting import Report, XmlBackend, JsonBackend, save_report, load_report, load_reports_from_dir
from lemoncheesecake.reporting.backends.xml import \
    save_report_into_file as save_xml, \
    load_report_from_file as load_xml
from lemoncheesecake.reporting.backends.json_ import \
    save_report_into_file as save_json, \
    load_report_from_file as load_json

from helpers.report import assert_report


@pytest.fixture()
def sample_report():
    report = Report()
    ts = time.time()
    report.start_time = ts
    report.end_time = ts
    report.report_generation_time = ts
    return report


def _test_save_report(tmpdir, sample_report, backend, load_func):
    filename = tmpdir.join("report").strpath
    save_report(filename, sample_report, backend)
    report = load_func(filename)
    assert_report(report, sample_report)


def test_save_report_json(tmpdir, sample_report):
    _test_save_report(tmpdir, sample_report, JsonBackend(), load_json)


def _test_load_report(tmpdir, sample_report, save_func):
    filename = tmpdir.join("report").strpath
    save_func(sample_report, filename)
    report = load_report(filename)
    assert_report(report, sample_report)


def test_load_report_json(tmpdir, sample_report):
    _test_load_report(tmpdir, sample_report, save_json)


def test_save_loaded_report(tmpdir, sample_report):
    filename = tmpdir.join("report").strpath
    save_json(sample_report, filename)

    loaded_report = load_report(filename)
    loaded_report.end_time += 1
    loaded_report.save()

    reloaded_report = load_report(filename)
    assert reloaded_report.end_time == loaded_report.end_time


try:
    import lxml
except ImportError:
    pass
else:
    def test_load_report_xml(tmpdir, sample_report):
        _test_load_report(tmpdir, sample_report, save_xml)

    def test_save_report_xml(tmpdir, sample_report):
        _test_save_report(tmpdir, sample_report, XmlBackend(), load_xml)

    def test_load_reports_from_dir(tmpdir, sample_report):
        save_xml(sample_report, tmpdir.join("report.xml").strpath)
        save_json(sample_report, tmpdir.join("report.js").strpath)
        tmpdir.join("report.txt").write("foobar")
        reports = list(load_reports_from_dir(tmpdir.strpath))
        assert_report(reports[0], sample_report)
        assert_report(reports[1], sample_report)
        assert "json" in [r.backend.name for r in reports]
        assert "xml" in [r.backend.name for r in reports]
