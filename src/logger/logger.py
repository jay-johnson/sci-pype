import syslog
import os
import sys
import logging
import logging.handlers


class Logger:

    def __init__(self, app_name, log_file, log_level):
        self.m_app_name  = app_name
        self.m_log_file  = log_file
        self.m_log_level = log_level
        self.m_logger    = logging.getLogger()

        try:
            handler = logging.handlers.SysLogHandler(address=log_file)
        except Exception, ex:

            print "\n\n\nFailed to initialize syslog for file(" + log_file + ") with Exception(" + str(ex) + ").  Exiting...\n\n"
            sys.exit(-1)
            return

        formatter = logging.Formatter('%(module)s %(levelname)s [%(process)d]: %(message)s')
        handler.setFormatter(formatter)

        self.m_logger.setLevel(self.m_log_level)
        self.m_logger.addHandler(handler)

        # ANSI Output colors
        self.m_HEADER     = '\033[95m'
        self.m_OKBLUE     = '\033[94m'
        self.m_OKGREEN    = '\033[92m'
        self.m_WARNING    = '\033[93m'
        self.m_FAIL       = '\033[91m'
        self.m_ENDC       = '\033[0m'

    # end of __init__

    
    def header(self, string_to_log):
        print self.m_HEADER + string_to_log + self.m_ENDC
        return None
    # end of header


    def blue(self, string_to_log):
        print self.m_OKBLUE + string_to_log + self.m_ENDC
        return None
    # end of blue


    def green(self, string_to_log):
        print self.m_OKGREEN + string_to_log + self.m_ENDC
        return None
    # end of green


    def warning(self, string_to_log):
        print self.m_WARNING + string_to_log + self.m_ENDC
        return None
    # end of warning


    def fail(self, string_to_log):
        print self.m_FAIL + string_to_log + self.m_ENDC
        return None
    # end of fail


    def debug(self, string_to_log):
        self.m_logger.debug(string_to_log)

    def error(self, string_to_log):
        self.m_logger.error(string_to_log)

    def info(self, string_to_log):
        self.m_logger.info(string_to_log)

    def warn(self, string_to_log):
        self.m_logger.warn(string_to_log)
    
    def crit(self, string_to_log):
        self.m_logger.critical(string_to_log)

    # per /usr/include/sys/syslog.h
    def log(self, string_to_log, level=6):

        #define LOG_INFO    6   /* informational */
        if level   == 6:
            self.m_logger.info(string_to_log)

        #define LOG_EMERG   0   /* system is unusable */
        #define LOG_ALERT   1   /* action must be taken immediately */
        #define LOG_CRIT    2   /* critical conditions */
        elif level <= 2:
            self.m_logger.critical(string_to_log)

        #define LOG_ERR     3   /* error conditions */
        elif level == 3:
            self.m_logger.error(string_to_log)

        #define LOG_WARNING 4   /* warning conditions */
        elif level == 4:
            self.m_logger.warning(string_to_log)

        #define LOG_NOTICE  5   /* normal but significant condition */
        elif level == 5:
            self.m_logger.info(string_to_log)

        #define LOG_DEBUG   7   /* debug-level messages */
        else:
            self.m_logger.debug(string_to_log)

        return None
    # end of log

# end of Logger
