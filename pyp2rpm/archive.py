import locale
import os
import re
import sys

from zipfile import ZipFile, ZipInfo
from tarfile import TarFile, TarInfo

from pyp2rpm import utils


class Archive(object):
    """Class representing package archive. All the operations must be run using with statement.
    For example:

    archive = Archive('/spam/beans.egg')
    with archive as a:
        a.get_contents_of_file('spam.py')
    """
    monkey_patched_zip = False

    @classmethod
    def monkey_patch_zip(cls):
        if not cls.monkey_patched_zip:
            # monkey patch ZipFile to behave like TarFile
            ZipFile.getmembers = ZipFile.infolist
            ZipFile.extractfile = ZipFile.open
            ZipFile.open = ZipFile
            ZipInfo.name = ZipInfo.filename
            cls.monkey_patched_zip = True

    def __init__(self, local_file):
        self.file = local_file
        self.name, self.suffix = os.path.splitext(local_file)
        self.handle = None
        self.monkey_patch_zip()

    @property
    def is_zip(self):
        return self.suffix in ['.egg', '.zip']

    @property
    def is_tar(self):
        return self.suffix in ['.tar', '.gz', '.bz2']

    @property
    def is_egg(self):
        return self.suffix == '.egg'

    def open(self):
        try:
            self.handle = self.extractor_cls.open(self.file)
        except BaseException as e: # TODO: log
            self.handle = None

        return self

    def close(self):
        if self.handle:
            self.handle.close()

    def __enter__(self):
        return self.open()

    def __exit__(self, type, value, traceback): # TODO: handle exceptions here
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
            pass
            # TODO: log that file has unextractable archive suffix and we can't look inside the archive

        return file_cls

    @utils.memoize_by_args
    def get_content_of_file(self, name, full_path = False): # TODO: log if file can't be opened
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
                if (full_path and member.name == name) or (not full_path and os.path.basename(member.name) == name):
                    extracted = self.handle.extractfile(member)
                    return extracted.read().decode(locale.getpreferredencoding())

        return None

    def has_file_with_suffix(self, suffixes): # TODO: maybe implement this using get_files_re
        """Finds out if there is a file with one of suffixes in the archive.
        Args:
            suffixes: list of suffixes or single suffix to look for
        Returns:
            True if there is at least one file with at least one given suffix in the archive, False otherwise (or archive can't be opened)
        """
        if not isinstance(suffixes, list):
            suffixes = [suffixes]

        if self.handle:
            for member in self.handle.getmembers():
                if os.path.splitext(member.name)[1] in suffixes:
                    return True
                else:
                    # hack for .zip files, where directories are not returned themselves, therefore we can't find e.g. .egg-info
                    for suffix in suffixes:
                        if '{0}/'.format(suffix) in member.name:
                            return True

        return False

    def get_files_re(self, file_re, full_path = False, ignorecase = False):
        """Finds all files that match file_re and returns their list.
        Doesn't return directories, only files.

        Args:
            file_re: raw string to match files against (gets compiled into re)
            full_path: whether to match against full path inside the archive or just the filenames
            ignorecase: whether to ignore case when using the given re
        Returns:
            List of full paths of files inside the archive that match the given file_re.
        """
        if ignorecase:
            compiled_re = re.compile(file_re, re.I)
        else:
            compiled_re = re.compile(file_re)

        found = []

        if self.handle:
            for member in self.handle.getmembers():
                if isinstance(member, TarInfo) and member.isdir():
                    pass # for TarInfo files, filter out directories
                elif (full_path and compiled_re.search(member.name)) or (not full_path and compiled_re.search(os.path.basename(member.name))):
                    found.append(member.name)

        return found

    def get_directories_re(self, directory_re, full_path = False, ignorecase = False):
        """Same as get_files_re, but for directories"""
        if ignorecase:
            compiled_re = re.compile(directory_re, re.I)
        else:
            compiled_re = re.compile(directory_re)

        found = set()

        if self.handle:
            for member in self.handle.getmembers():
                if isinstance(member, ZipInfo): # zipfiles only list directories => have to work around that
                    to_match = os.path.dirname(member.name)
                elif isinstance(member, TarInfo) and member.isdir(): # tarfiles => only match directories
                    to_match = member.name
                else:
                    to_match = None
                if to_match:
                    if (full_path and compiled_re.search(to_match)) or (not full_path and compiled_re.search(os.path.basename(to_match))):
                        found.add(to_match)

        return list(found)

    def find_list_argument(self, setup_argument):
        """A simple method that gets setup() function from setup.py list argument like install_requires.

        Will not work in all cases and might need a smarter approach.
        On the other side, it's so stupid, that it's actually smart - it gets this:
        'console_scripts': [
            'xtermcolor = xtermcolor.Main:Cli'
        ]
        as 'scripts', which is very nice :)

        Args:
            setup_argument: name of the argument of setup() function to get value of
        Returns:
            The requested setup() argument or empty list, if setup.py can't be open (or argument is not present).
        """
        setup_py = self.get_content_of_file('setup.py') # TODO: construct absolute path here?
        if not setup_py: return []

        argument = []
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
            argument[-1] = argument[-1][:argument[-1].rfind(']')+1]
            argument[-1] = argument[-1].rstrip().rstrip(',')
            try:
                return eval(' '.join(argument).strip())
            except: # something unparsable in the list - different errors can come out - function undefined, syntax error, ...
                return []

    def has_argument(self, argument):
        """A simple method that finds out if setup() function from setup.py is called with given argument.
        Args:
            argument: argument to look for
        Returns:
            True if argument is used, False otherwise
        """
        setup_py = self.get_content_of_file('setup.py')
        if not setup_py: return False

        argument_re = re.compile(r'setup\(.*(?<!\w){0}.*\)'.format(argument), re.DOTALL)

        return True if argument_re.search(setup_py) else False
