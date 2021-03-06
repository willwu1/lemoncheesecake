'''
Created on Nov 17, 2016

@author: nicolas
'''

import pytest

from lemoncheesecake.reporting.backends.xml import XmlBackend, load_report_from_file
from lemoncheesecake.exceptions import InvalidReportFile


try:
    import lxml
except ImportError:
    pass
else:
    from helpers.reporttests import *  # import the actual tests against XML serialization

    @pytest.fixture(scope="function")
    def backend():
        return XmlBackend()

    @pytest.fixture()
    def serialization_tester():
        return do_test_serialization

    def test_load_report_non_xml(tmpdir):
        file = tmpdir.join("report.xml")
        file.write("foobar")
        with pytest.raises(InvalidReportFile):
            load_report_from_file(file.strpath)

    def test_load_report_bad_xml(tmpdir):
        file = tmpdir.join("report.xml")
        file.write("<value>foobar</value>")
        with pytest.raises(InvalidReportFile):
            load_report_from_file(file.strpath)