'''
Created on Mar 18, 2016

@author: nicolas
'''

import time
import sys

IS_PYTHON3 = sys.version_info > (3,)

class LemonCheesecakeException(Exception):
    message_prefix = None
    
    def __str__(self):
        s = Exception.__str__(self)
        if self.message_prefix:
            s = "%s: %s" % (self.message_prefix, s)
        return s

class LemonCheesecakeInternalError(Exception):
    def __str__(self):
        return "Internal error: %s" % Exception.__str__(self)

class LemonCheesecakeInvalidReport(LemonCheesecakeException):
    pass

def humanize_duration(duration):
    ret = ""
    
    if duration / 3600 >= 1:
        ret += ("%02dh" if ret else "%dh") % (duration / 3600)
        duration %= 3600
    
    if duration / 60 >= 1:
        ret += ("%02dm" if ret else "%dm") % (duration / 60)
        duration %= 60
    
    if duration >= 1:
        ret += ("%02ds" if ret else "%ds") % duration
    
    if not ret:
        ret = "0s"
    
    return ret

def reporting_dir_with_datetime(report_rootdir, t):
    return time.strftime("report-%Y%m%d-%H%M%S", time.localtime(t))