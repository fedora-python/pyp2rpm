import os
import re

from zipfile import ZipFile, ZipInfo
from tarfile import TarFile

from pyp2rpmlib import utils

# monkey patch ZipFile to behave like TarFile
ZipFile.getmembers = ZipFile.infolist
ZipFile.extractfile = ZipFile.open
ZipFile.open = ZipFile
ZipInfo.name = ZipInfo.filename


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
                    return extracted.read()

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
                        if '%s/' % suffix in member.name:
                            return True

        return False

    def get_files_re(self, file_re, full_path = False, ignorecase = False):
        """Finds all files that match file_re and returns their list.
        Doesn't care about directories!

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
                if (full_path and compiled_re.search(member.name)) or (not full_path and compiled_re.search(os.path.basename(member.name))):
                    found.append(member.name)

        return found

    def find_list_argument(self, setup_argument):
        """A simple method that gets setup() function from setup.py list argument like install_requires.

        Will not work in all cases and might need a smarter approach.

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
            if line.find(setup_argument) != -1 or cont:
                start_braces += line.count('[')
                end_braces += line.count(']')

                cont = True
                argument.append(line)
                if start_braces == end_braces:
                    break

        if not argument:
            return []
        else:
            argument[0] = argument[0][argument[0].find('['):]
            argument[-1] = argument[-1].rstrip().rstrip(',')
            return eval(' '.join(argument).strip())
