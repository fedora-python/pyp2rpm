import os
import sys
import logging
import json
import runpy
from subprocess import Popen, PIPE
from abc import ABCMeta

from pyp2rpm import utils
from pyp2rpm import main_dir
from pyp2rpm import settings
from pyp2rpm.exceptions import ExtractionError
from command import extract_dist

logger = logging.getLogger(__name__)


class ModuleRunner(object):
    """Abstract base class for module runners."""

    __metaclass__ = ABCMeta

    def __init__(self, module, *args):
        self.dirname = os.path.dirname(module)
        self.filename = os.path.basename(module)
        self.args = args


class RunpyModuleRunner(ModuleRunner):
    """Runs given module in current interpreter using runpy."""
    @staticmethod
    def not_suffixed(module):
        if module.endswith('py'):
            return module[:-3]

    def run(self):
        """Executes the code of the specified module."""
        with utils.ChangeDir(self.dirname):
            sys.path.insert(0, self.dirname)
            sys.argv[1:] = self.args
            runpy.run_module(self.not_suffixed(self.filename), run_name='__main__', alter_sys=True)

    @property
    def results(self):
        return extract_dist.extract_dist.class_metadata


class SubprocessModuleRunner(ModuleRunner):
    """Runs module in external interpreter using subprocess."""

    def run(self, interpreter):
        """Executes the code of the specified module. Deserializes captured json data."""
        with utils.ChangeDir(self.dirname):
            command_list = ['PYTHONPATH=' + main_dir, interpreter, self.filename] + list(self.args)
            try:
                proc = Popen(' '.join(command_list), stdout=PIPE, stderr=PIPE, shell=True)
                stream_data = proc.communicate()
            except Exception as e:
                logger.error("Error {0} while executing extract_dist command.".format(e))
                raise ExtractionError
            stream_data = [utils.console_to_str(s) for s in stream_data]
            if proc.returncode:
                logger.error('Subprocess failed, stdout: {0[0]}, stderr: {0[1]}'.format(
                    stream_data))
            self._result = json.loads(stream_data[0].split("extracted json data:\n")[-1])

    @property
    def results(self):
        try:
            return self._result
        except AttributeError:
            return None
