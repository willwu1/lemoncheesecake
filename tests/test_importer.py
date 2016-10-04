import os.path

import pytest

from lemoncheesecake.launcher import importer
from lemoncheesecake.exceptions import *
from helpers import build_test_module

def test_import_testsuite_from_file(tmpdir):
    file = tmpdir.join("mytestsuite.py")
    file.write(build_test_module())
    klass = importer.import_testsuite_from_file(file.strpath)
    assert klass.__name__ == "mytestsuite"

def test_import_testsuite_from_file_invalid_module(tmpdir):
    file = tmpdir.join("doesnotexist.py")
    with pytest.raises(ImportTestSuiteError):
        importer.import_testsuite_from_file(file.strpath)

def test_import_testsuite_from_file_invalid_class(tmpdir):
    file = tmpdir.join("anothertestsuite.py")
    file.write(build_test_module())
    with pytest.raises(ImportTestSuiteError):
        importer.import_testsuite_from_file(file.strpath)

def test_import_testsuites_from_directory_without_modules(tmpdir):
    klasses = importer.import_testsuites_from_directory(tmpdir.strpath)
    assert len(klasses) == 0

def test_import_testsuites_from_directory_with_modules(tmpdir):
    names = []
    for i in range(3):
        name = "mytestsuite%d" % i
        names.append(name)
        tmpdir.join("%s.py" % name).write(build_test_module(name))
    klasses = importer.import_testsuites_from_directory(tmpdir.strpath)
    for name in names:
        assert name in [k.__name__ for k in klasses]

def test_import_testsuites_from_directory_with_subdir(tmpdir):
    file = tmpdir.join("parentsuite.py")
    file.write(build_test_module("parentsuite"))
    subdir = tmpdir.join("parentsuite")
    subdir.mkdir()
    file = subdir.join("childsuite.py")
    file.write(build_test_module("childsuite"))
    klasses = importer.import_testsuites_from_directory(tmpdir.strpath)
    assert klasses[0].__name__ == "parentsuite"
    assert len(klasses[0].sub_suites) == 1