import logging
import os
import sys


logger = logging.getLogger('pyp2rpm')
logger.setLevel(logging.DEBUG)

file_formatter = logging.Formatter(u'%(asctime)s::%(name)s::%(levelname)s::%(message)s')
console_formatter = logging.Formatter(u'%(levelname)s  %(message)s')


class LoggerWriter(object):
    """Allows to redirect stream to logger"""

    def __init__(self, level):
        self.level = level
        self.errors = None

    def write(self, message):
        if message not in ('\n', ''):
            self.level(message.rstrip('\n'))

    def flush(self):
        pass


class LevelFilter(logging.Filter):

    def __init__(self, level):
        super(LevelFilter, self).__init__(level)
        self.level = level

    def filter(self, record):
        return record.levelno == self.level


def register_file_log_handler(log_file, level=logging.DEBUG, fmt=file_formatter):
    dirname = os.path.dirname(log_file)
    try:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    except (OSError, IOError):
        return False
    try:
        file_handler = logging.FileHandler(log_file, 'a')
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except (OSError, IOError):
        return False
    return True


def register_console_log_handler(level=logging.INFO, fmt=console_formatter):
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)
