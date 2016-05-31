import json
import locale
import logging
import os
import re
import sre_constants
import string

from zipfile import ZipFile, ZipInfo
from tarfile import TarFile, TarInfo

from pyp2rpm import utils

logger = logging.getLogger(__name__)


def generator_to_list(fn):
    """This decorator is for flat_list function.
    It converts returned generator to list.
    """
    def wrapper(*args, **kw):
        return list(fn(*args, **kw))
    return wrapper


@generator_to_list
def flat_list(lst):
    """This function flatten given nested list.
    Argument:
        nested list
    Returns:
        flat list
    """
    if isinstance(lst, list):
        for item in lst:
            for i in flat_list(item):
                yield i
    else:
        yield lst


class ZipWrapper(object):
    """wrapps ZipFile to behave like TarFile"""

    def __init__(self, obj):
        if not isinstance(obj, ZipFile):
            raise TypeError("Object must be ZipFile, type of {} is {}".format(
                obj, type(obj)))
        self._wrapped_obj = obj

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        return getattr(self._wrapped_obj, attr)

    def getmembers(self, *args, **kwargs):
        return self._wrapped_obj.infolist(*args, **kwargs)

    def extractfile(self, *args, **kwargs):
        return self._wrapped_obj.open(*args, **kwargs)

    def open(self, *args, **kwargs):
        return self._wrapped_obj(*args, **kwargs)


class Archive(object):

    """Class representing package archive. All the operations must be run using with statement.
    For example:

    archive = Archive('/spam/beans.egg')
    with archive as a:
        a.get_contents_of_file('spam.py')
    """

    def __init__(self, local_file):
        self.file = local_file
        self.name, self.suffix = os.path.splitext(local_file)
        self.handle = None
        ZipInfo.name = ZipInfo.filename

    @property
    def is_zip(self):
        return self.suffix in ['.egg', '.zip', '.whl']

    @property
    def is_tar(self):
        return self.suffix in ['.tar', '.gz', '.bz2', '.tgz', '.xz']

    @property
    def is_egg(self):
        return self.suffix == '.egg'

    @property
    def is_wheel(self):
        return self.suffix == '.whl'

    def open(self):
        try:
            if self.extractor_cls == ZipFile:
                self.handle = ZipWrapper(self.extractor_cls(self.file))
            else:
                self.handle = self.extractor_cls.open(self.file)
        except BaseException:
            self.handle = None
            logger.error('Failed to open archive: {0}.'.format(self.file), exc_info=True)

        return self

    def close(self):
        if self.handle:
            self.handle.close()

    def __enter__(self):
        return self.open()

    def __exit__(self, type, value, traceback):  # TODO: handle exceptions here
        self.close()

    @property
    def extractor_cls(self):
        """Returns the class that can read this archive based on archive suffix.
        Returns:
            Class that can read this archive or None if no such exists.
        """
        file_cls = None

        # only catches ".gz", even from ".tar.gz"
        if self.is_tar:
            file_cls = TarFile
        elif self.is_zip:
            file_cls = ZipFile
        else:
            logger.info("Couldn't recognize archive suffix: {0}.".format(self.suffix))

        return file_cls

    @utils.memoize_by_args
    def get_content_of_file(self, name, full_path=False):  # TODO: log if file can't be opened
        """Returns content of file from archive.

        If full_path is set to False and two files with given name exist,
        content of one is returned (it is not specified which one that is).
        If set to True, returns content of exactly that file.

        Args:
            name: name of the file to get content of
        Returns:
            Content of the file with given name or None, if no such.
        """
        if self.handle:
            for member in self.handle.getmembers():
                if (full_path and member.name == name)\
                        or (not full_path and os.path.basename(member.name) == name):
                    extracted = self.handle.extractfile(member)
                    return extracted.read().decode(locale.getpreferredencoding())

        return None

    def extract_file(self, name, full_path=False, directory="."):
        """Extract a member from the archive to the specified working directory.
        Behaviour of name and pull_path is the same as in function get_content_of_file.
        """
        if self.handle:
            for member in self.handle.getmembers():
                if (full_path and member.name == name or
                        not full_path and os.path.basename(member.name) == name):
                    self.handle.extract(member, path=directory)   # TODO handle KeyError exception

    def extract_all(self, directory=".", members=None):
        """Extract all member from the archive to the specified working directory."""
        if self.handle:
            self.handle.extractall(path=directory, members=members)

    def has_file_with_suffix(self, suffixes):  # TODO: maybe implement this using get_files_re
        """Finds out if there is a file with one of suffixes in the archive.
        Args:
            suffixes: list of suffixes or single suffix to look for
        Returns:
            True if there is at least one file with at least one given suffix in the archive,
            False otherwise (or archive can't be opened)
        """
        if not isinstance(suffixes, list):
            suffixes = [suffixes]

        if self.handle:
            for member in self.handle.getmembers():
                if os.path.splitext(member.name)[1] in suffixes:
                    return True
                else:
                    # hack for .zip files, where directories are not returned
                    # themselves, therefore we can't find e.g. .egg-info
                    for suffix in suffixes:
                        if '{0}/'.format(suffix) in member.name:
                            return True

        return False

    def get_files_re(self, file_re, full_path=False, ignorecase=False):
        """Finds all files that match file_re and returns their list.
        Doesn't return directories, only files.

        Args:
            file_re: raw string to match files against (gets compiled into re)
            full_path: whether to match against full path inside the archive or just the filenames
            ignorecase: whether to ignore case when using the given re
        Returns:
            List of full paths of files inside the archive that match the given file_re.
        """
        try:
            if ignorecase:
                compiled_re = re.compile(file_re, re.I)
            else:
                compiled_re = re.compile(file_re)
        except sre_constants.error:
            logger.error("Failed to compile regex: {}.".format(file_re))
            return []

        found = []

        if self.handle:
            for member in self.handle.getmembers():
                if isinstance(member, TarInfo) and member.isdir():
                    pass  # for TarInfo files, filter out directories
                elif (full_path and compiled_re.search(member.name))\
                        or (not full_path and compiled_re.search(os.path.basename(member.name))):
                    found.append(member.name)

        return found

    def get_directories_re(self, directory_re, full_path=False, ignorecase=False):
        """Same as get_files_re, but for directories"""
        if ignorecase:
            compiled_re = re.compile(directory_re, re.I)
        else:
            compiled_re = re.compile(directory_re)

        found = set()

        if self.handle:
            for member in self.handle.getmembers():
                # zipfiles only list directories => have to work around that
                if isinstance(member, ZipInfo):
                    to_match = os.path.dirname(member.name)
                # tarfiles => only match directories
                elif isinstance(member, TarInfo) and member.isdir():
                    to_match = member.name
                else:
                    to_match = None
                if to_match:
                    if ((full_path and compiled_re.search(to_match))
                            or (not full_path and compiled_re.search(os.path.basename(to_match)))):
                        found.add(to_match)

        return list(found)

    def find_list_argument(self, setup_argument):
        """A simple method that gets setup() function from setup.py list argument
           like install_requires.

        Will not work in all cases and might need a smarter approach.
        On the other side, it's so stupid, that it's actually smart - it gets this:
        'console_scripts': [
            'xtermcolor = xtermcolor.Main:Cli'
        ]
        as 'scripts', which is very nice :)

        Args:
            setup_argument: name of the argument of setup() function
                            to get value of
        Returns:
            The requested setup() argument or empty list, if setup.py
            can't be open (or argument is not present).
        """
        argument = []
        cont = False
        setup_cfg = self.get_content_of_file('setup.cfg')
        if setup_cfg:
            argument_re = re.compile(r'\b' + format(setup_argument) + '\s*=')
            for line in setup_cfg.splitlines():
                if line.find("#") != -1:
                    line = line.split("#")[0]
                if argument_re.search(line):
                    args = line.split("=")
                    if len(args) > 1:
                        argument.append(args[1])
                    cont = True
                    continue
                if cont and len(line) and line[0] in string.whitespace:
                    argument.append(line.strip())
                    continue
                if cont:
                    return argument

        setup_py = self.get_content_of_file(
            'setup.py')  # TODO: construct absolute path here?
        if not setup_py:
            return []

        start_braces = end_braces = 0
        cont = False

        for line in setup_py.splitlines():
            if setup_argument in line or cont:
                if line.find("#") != -1:
                    line = line.split("#")[0]
                start_braces += line.count('[')
                end_braces += line.count(']')

                cont = True
                argument.append(line)
                if start_braces == end_braces:
                    break
        if not argument or start_braces == 0:
            return []
        else:
            argument[0] = argument[0][argument[0].find('['):]
            argument[-1] = argument[-1][:argument[-1].rfind(']') + 1]
            argument[-1] = argument[-1].rstrip().rstrip(',')
            try:
                return flat_list(eval(' '.join(argument).strip()))
            # something unparsable in the list - different errors can come out -
            # function undefined, syntax error, ...
            except:
                logger.warn('Something unparsable in the list.', exc_info=True)
                return []

    def has_argument(self, argument):
        """A simple method that finds out if setup() function from setup.py
           is called with given argument.
        Args:
            argument: argument to look for
        Returns:
            True if argument is used, False otherwise
        """
        setup_cfg = self.get_content_of_file('setup.cfg')
        if setup_cfg:
            argument_re = re.compile(r'\b' + format(argument) + '\s*=')
            if argument_re.search(setup_cfg):
                return True

        setup_py = self.get_content_of_file('setup.py')
        if not setup_py:
            return False

        argument_re = re.compile(
            r'setup\(.*(?<!\w){0}.*\)'.format(argument), re.DOTALL)

        return True if argument_re.search(setup_py) else False

    @property
    def json_wheel_metadata(self):
        """Simple getter that get content of metadata.json file in .whl archive
        Returns:
            metadata from metadata.json in json format
        """
        try:
            json_file = json.loads(self.get_content_of_file('metadata.json'))
        except TypeError:
            json_file = json.loads(self.get_content_of_file('pydist.json'))
        return json_file

    def wheel_description(self):
        """Get content of DESCRIPTION file in .whl archive"""
        return self.get_content_of_file('DESCRIPTION.rst')

    @property
    def record(self):
        """Getter that get content of RECORD file in .whl archive
        Returns:
            dict with keys `modules` and `scripts`
        """

        modules = []
        scripts = []
        if self.get_content_of_file('RECORD'):
            lines = self.get_content_of_file('RECORD').splitlines()
            for line in lines:
                if 'dist-info' in line or '/' not in line:
                    continue
                elif '.data/scripts' in line:
                    script = line.split(',', 1)[0]
                    # strip Name.version.data/scripts/
                    scripts.append(re.sub('.*/.*/', '', script))
                else:
                    # strip everything from first occurance of slash
                    modules.append(re.sub('/.*', '', line))

        return {'modules': set(modules), 'scripts': set(scripts)}
