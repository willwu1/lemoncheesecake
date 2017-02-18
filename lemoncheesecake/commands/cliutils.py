'''
Created on Feb 17, 2017

@author: nicolas
'''

from termcolor import colored
from terminaltables import AsciiTable

def bold(s):
    return colored(s, attrs=["bold"])

def print_table(title, headers, lines):
    if lines:
        print "%s:" % title
        print AsciiTable([headers] + lines).table
    else:
        print "%s: <none>" % title
    print
