'''
Created on Jan 7, 2017

@author: nicolas
'''

import inspect
import re

from lemoncheesecake.loader import import_module, get_matching_files, get_py_files_from_dir
from lemoncheesecake.exceptions import FixtureError, ProgrammingError
from lemoncheesecake.utils import get_distincts_in_list

__all__ = ("fixture", "load_fixtures_from_func")

FORBIDDEN_FIXTURE_NAMES = ("fixture_name", )

def import_fixtures_from_file(filename):
    mod = import_module(filename)
    funcs = []
    for sym_name in dir(mod):
        sym = getattr(mod, sym_name)
        if hasattr(sym, "_lccfixtureinfo"):
            funcs.append(sym)
    return funcs

def import_fixtures_from_files(patterns, excluding=[]):
    """
    Import fixtures from a list of files:
    - patterns: a mandatory list (a simple string can also be used instead of a single element list)
      of files to import; the wildcard '*' character can be used
    - exclude: an optional list (a simple string can also be used instead of a single element list)
      of elements to exclude from the expanded list of files to import
    Example: import_testsuites_from_files("test_*.py")
    """
    fixtures = []
    for file in get_matching_files(patterns, excluding):
        fixtures.extend(import_fixtures_from_file(file))
    return fixtures

def import_fixtures_from_directory(dir):
    fixtures = []
    for file in get_py_files_from_dir(dir):
        fixtures.extend(import_fixtures_from_file(file))
    return fixtures

class FixtureInfo:
    def __init__(self, names, scope):
        self.names = names
        self.scope = scope

def fixture(names=None, scope="test"):
    if scope not in ("test", "testsuite", "session", "session_prerun"):
        raise ProgrammingError("Invalid fixture scope '%s'" % scope)
    
    def wrapper(func):
        setattr(func, "_lccfixtureinfo", FixtureInfo(names, scope))
        return func
    
    return wrapper

def get_fixture_names(func):
    return func._lccfixtureinfo.names or [func.__name__]

def get_fixture_name(func):
    return get_fixture_names(func)[0]

def get_fixture_aliases(func):
    return get_fixture_names(func)[1:]

def get_fixture_scope(func):
    return func._lccfixtureinfo.scope

def get_fixture_params(func):
    return inspect.getargspec(func).args

def get_fixture_doc(func):
    return re.sub("\n\s+", "\\\\n ", func.__doc__) if func.__doc__ else None

class BaseFixture:
    def is_builtin(self):
        return False
    
    def get_scope_level(self):
        return {
            "test": 1,
            "testsuite": 2,
            "session": 3,
            "session_prerun": 4
        }[self.scope]

    def is_executed(self):
        return hasattr(self, "_result")

    def teardown(self):
        pass
    
    def reset(self):
        pass
    
class Fixture(BaseFixture):
    def __init__(self, name, func, scope, params):
        self.name = name
        self.func = func
        self.scope = scope
        self.params = params
        self._generator = None

    def execute(self, params={}):
        assert not self.is_executed(), "fixture '%s' has already been executed" % self.name
        for param_name in params.keys():
            assert param_name in self.params

        result = self.func(**params)
        if inspect.isgenerator(result):
            self._generator = result
            self._result = next(result)
        else:
            self._result = result
    
    def get_result(self):
        assert self.is_executed(), "fixture '%s' has not been executed" % self.name
        return self._result
    
    def teardown(self):
        assert self.is_executed(), "fixture '%s' has not been executed" % self.name
        delattr(self, "_result")
        if self._generator:
            try:
                next(self._generator)
            except StopIteration:
                self._generator = None
            else:
                raise FixtureError("The fixture yields more than once, only one yield is supported") 
    
class BuiltinFixture(BaseFixture):
    def __init__(self, name, value):
        self.name = name
        self.scope = "session_prerun"
        self.params = []
        self._value = value
    
    def is_builtin(self):
        return True
        
    def execute(self, params={}):
        self._result = self._value() if callable(self._value) else self._value
    
    def get_result(self):
        return self._result

def load_fixtures_from_func(func):
    assert hasattr(func, "_lccfixtureinfo")
    names = func._lccfixtureinfo.names
    if not names:
        names = [func.__name__]
    scope = func._lccfixtureinfo.scope
    params = inspect.getargspec(func).args
    return [Fixture(name, func, scope, params) for name in names]

class FixtureRegistry:
    def __init__(self):
        self._fixtures = {}
    
    def add_fixture(self, fixture):
        if fixture.name in self._fixtures and self._fixtures[fixture.name].is_builtin():
            raise FixtureError("'%s' is a builtin fixture name" % fixture.name)
        self._fixtures[fixture.name] = fixture
    
    def add_fixtures(self, fixtures):
        for fixture in fixtures:
            self.add_fixture(fixture)
    
    def get_fixture(self, name):
        return self._fixtures[name]
    
    def _get_fixture_dependencies(self, name, orig_fixture):
        fixture_params = [p for p in self._fixtures[name].params if p != "fixture_name"]
        if orig_fixture and orig_fixture in fixture_params:
            raise FixtureError("Fixture '%s' has a circular dependency on fixture '%s'" % (orig_fixture, name))

        dependencies = []
        for param in fixture_params:
            if param not in self._fixtures:
                raise FixtureError("Fixture '%s' used by fixture '%s' does not exist" % (param, name))
            dependencies.extend(self._get_fixture_dependencies(param, orig_fixture if orig_fixture else name)) 
        dependencies.extend(fixture_params)
        
        return dependencies
    
    def get_fixture_dependencies(self, name):
        dependencies = self._get_fixture_dependencies(name, None)
        return get_distincts_in_list(dependencies)
    
    def filter_fixtures(self, base_names=[], scope=None, is_executed=None, with_dependencies=False):
        def do_filter_fixture(fixture):
            if scope != None and fixture.scope != scope:
                return False
            if is_executed != None and fixture.is_executed() != is_executed:
                return False
            return True
        
        names = base_names if base_names else self._fixtures.keys()
        fixtures = filter(do_filter_fixture, [self._fixtures[name] for name in names])
        return [f.name for f in fixtures]
    
    def check_dependencies(self):
        """
        Checks for:
        - missing dependencies
        - circular dependencies
        - scope incoherence
        - forbidden fixture name
        raises FixtureError if a check fails
        """
        # first, check for forbidden fixture name
        for fixture_name in self._fixtures.keys():
            if fixture_name in FORBIDDEN_FIXTURE_NAMES:
                raise FixtureError("Fixture name '%s' is forbidden" % fixture_name)
        
        # second, check for missing & circular dependencies
        for fixture_name in self._fixtures.keys():
            self.get_fixture_dependencies(fixture_name)
        
        # third, check fixture scope compliance with their direct fixture dependencies
        for fixture in self._fixtures.values():
            dependency_fixtures = [self._fixtures[param] for param in fixture.params if param != "fixture_name"]
            for dependency_fixture in dependency_fixtures:
                if dependency_fixture.get_scope_level() < fixture.get_scope_level():
                    raise FixtureError("Fixture '%s' with scope '%s' is incompatible with scope '%s' of fixture '%s'" % (
                        fixture.name, fixture.scope, dependency_fixture.scope, dependency_fixture.name
                    ))
        
    
    def check_fixtures_in_test(self, test, suite):
        for fixture in test.get_params():
            if fixture not in self._fixtures:
                raise FixtureError("Unknown fixture '%s' used in test '%s'" % (fixture, test.get_path_str()))
        
    def check_fixtures_in_testsuite(self, suite):
        for test in suite.get_tests():
            self.check_fixtures_in_test(test, suite)
        
        for sub_suite in suite.get_sub_testsuites():
            self.check_fixtures_in_testsuite(sub_suite)
    
    def check_fixtures_in_testsuites(self, suites):
        for suite in suites:
            self.check_fixtures_in_testsuite(suite)

    def get_fixture_scope(self, name):
        return self._fixtures[name].scope
    
    def execute_fixture(self, name):
        fixture = self._fixtures[name]
        params = {}
        for param in fixture.params:
            if param == "fixture_name":
                params["fixture_name"] = name
            else:
                dependency_fixture = self._fixtures[param]
                if not dependency_fixture.is_executed():
                    self.execute_fixture(dependency_fixture.name)
                params[dependency_fixture.name] = dependency_fixture.get_result()
        fixture.execute(params)
        
    def get_fixture_result(self, name):
        return self._fixtures[name].get_result()
    
    def is_fixture_executed(self, name):
        return self._fixtures[name].is_executed()
    
    def get_fixture_results_as_params(self, names):
        results = {}
        for name in names:
            results[name] = self.get_fixture_result(name)
        return results
    
    def teardown_fixture(self, name):
        self._fixtures[name].teardown()