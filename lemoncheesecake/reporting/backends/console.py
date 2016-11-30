'''
Created on Mar 19, 2016

@author: nicolas
'''

from __future__ import print_function

import sys
import re

from lemoncheesecake.reporting.backend import ReportingBackend, ReportingSession
from lemoncheesecake.utils import IS_PYTHON3, humanize_duration
from lemoncheesecake.reporting.backends import terminalsize

from colorama import init, Style, Fore
from termcolor import colored

class LinePrinter:
    def __init__(self, terminal_width):
        self.terminal_width = terminal_width
        self.prev_len = 0
    
    def print_line(self, line, force_len=None):
        value_len = force_len if force_len else len(line) 
        if not IS_PYTHON3:
            if type(line) is unicode:
                line = line.encode("utf-8")
        
        if value_len > self.terminal_width:
            line = line[:self.terminal_width-4] + "..."
        
        sys.stdout.write("\r")
        sys.stdout.write(line)
        if self.prev_len > value_len:
            sys.stdout.write(" " * (self.prev_len - value_len))
        sys.stdout.flush()
        
        self.prev_len = value_len
    
    def new_line(self):
        self.prev_len = 0
        sys.stdout.write("\n")
        sys.stdout.flush()
    
    def erase_line(self):
        sys.stdout.write("\r")
        sys.stdout.write(" " * self.prev_len)
        sys.stdout.write("\r")
        self.prev_len = 0

CTX_BEFORE_SUITE = 0
CTX_TEST = 1
CTX_AFTER_SUITE = 2

class ConsoleReportingSession(ReportingSession):
    def __init__(self, report, report_dir, terminal_width):
        ReportingSession.__init__(self, report, report_dir)
        init() # init colorama
        self.lp = LinePrinter(terminal_width)
        self.terminal_width = terminal_width
        self.context = None
    
    def begin_tests(self):
        self.previous_obj = None
 
    def begin_before_suite(self, testsuite):
        self.context = CTX_BEFORE_SUITE
        self.current_test_idx = 1

        if not testsuite.has_selected_tests(deep=False):
            return

        if self.previous_obj:
            sys.stdout.write("\n")

        path = testsuite.get_path_str()
        path_len = len(path)
        max_width = min((self.terminal_width, 80))
        padding_total = max_width - 2 - path_len if path_len <= (max_width - 2) else 0 # -2 corresponds to the two space characters at the left and right of testsuite path
        padding_left = padding_total / 2
        padding_right = padding_total / 2 + padding_total % 2
        sys.stdout.write("=" * padding_left + " " + colored(testsuite.get_path_str(), attrs=["bold"]) + " " + "=" * padding_right + "\n")
        self.previous_obj = testsuite
    
    def end_before_suite(self, testsuite):
        self.lp.erase_line()
        
    def begin_after_suite(self, testsuite):
        self.context = CTX_AFTER_SUITE
    
    def end_after_suite(self, testsuite):
        self.lp.erase_line()
        self.context = None
        
    def begin_test(self, test):
        self.context = CTX_TEST
        self.current_test_line = " -- %2s # %s" % (self.current_test_idx, test.id)
        self.lp.print_line(self.current_test_line + "...")
        self.previous_obj = test
    
    def end_test(self, test, outcome):
        line = " %s %2s # %s" % (
            colored("OK", "green", attrs=["bold"]) if outcome else colored("KO", "red", attrs=["bold"]),
            self.current_test_idx, test.id
        )
        raw_line = "%s %2s # %s" % ("OK" if outcome else "KO", self.current_test_idx, test.id)
        self.lp.print_line(line, force_len=len(raw_line))
        self.lp.new_line()
        self.current_test_idx += 1
    
    def set_step(self, description):
        if self.context == CTX_BEFORE_SUITE:
            self.lp.print_line(" => before suite: %s" % description)
        elif self.context == CTX_AFTER_SUITE:
            self.lp.print_line(" => after suite: %s" % description)
        elif self.context == CTX_TEST:
            description += "..."
            line = "%s (%s)" % (self.current_test_line, description)
            self.lp.print_line(line)
    
    def log(self, content, level):
        pass
    
    def end_tests(self):
        report = self.report
        stats = report.get_stats()
        print()
        print(colored("Statistics", attrs=["bold"]), ":")
        print(" * Duration: %s" % humanize_duration(report.end_time - report.start_time))
        print(" * Tests: %d" % stats.tests)
        print(" * Successes: %d (%d%%)" % (stats.test_successes, float(stats.test_successes) / stats.tests * 100 if stats.tests else 0))
        print(" * Failures: %d" % (stats.test_failures))
        print()

class ConsoleBackend(ReportingBackend):
    name = "console"
    
    def __init__(self):
        width, height = terminalsize.get_terminal_size()
        self.terminal_width = width

    def create_reporting_session(self, report, report_dir):
        return ConsoleReportingSession(report, report_dir, self.terminal_width)
