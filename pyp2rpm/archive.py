import json
import locale
import logging
import os
import re
import sre_constants
import sys

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

    def getnames(self, *args, **kwargs):
        return self._wrapped_obj.namelist(*args, **kwargs)

    def extractfile(self, *args, **kwargs):
        return self._wrapped_obj.open(*args, **kwargs)

    def open(self, *args, **kwargs):
        return self._wrapped_obj(*args, **kwargs)


class Archive(object):

    """Class representing package archive. All the operations must be run using
    with statement.
    For example:

    archive = Archive('/spam/beans.egg')
    with archive as a:
        a.get_contents_of_file('spam.py')
    """

    def __init__(self, local_file):
        self.file = local_file
        self.name = os.path.basename(local_file)
        self.suffix = os.path.splitext(local_file)[1]
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
            logger.error('Failed to open archive: {0}.'.format(
                self.file), exc_info=True)

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
            logger.info("Couldn't recognize archive suffix: {0}.".format(
                self.suffix))

        return file_cls

    @utils.memoize_by_args
    # TODO: log if file can't be opened
    def get_content_of_file(self, name, full_path=False):
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
                if (full_path and member.name == name) or (
                        not full_path and os.path.basename(
                            member.name) == name):
                    extracted = self.handle.extractfile(member)
                    return extracted.read().decode(
                        locale.getpreferredencoding())

        return None

    def extract_file(self, name, full_path=False, directory="."):
        """Extract a member from the archive to the specified working directory.
        Behaviour of name and pull_path is the same as in function
        get_content_of_file.
        """
        if self.handle:
            for member in self.handle.getmembers():
                if (full_path and member.name == name or
                        not full_path and os.path.basename(
                            member.name) == name):
                    # TODO handle KeyError exception
                    self.handle.extract(member, path=directory)

    def extract_all(self, directory=".", members=None):
        """Extract all member from the archive to the specified working
        directory.
        """
        if self.handle:
            self.handle.extractall(path=directory, members=members)

    # TODO: maybe implement this using get_files_re
    def has_file_with_suffix(self, suffixes):
        """Finds out if there is a file with one of suffixes in the archive.
        Args:
            suffixes: list of suffixes or single suffix to look for
        Returns:
            True if there is at least one file with at least one given suffix
            in the archive, False otherwise (or archive can't be opened)
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
            full_path: whether to match against full path inside the archive
            or just the filenames
            ignorecase: whether to ignore case when using the given re
        Returns:
            List of full paths of files inside the archive that match the given
            file_re.
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
                elif (full_path and compiled_re.search(member.name)) or (
                    not full_path and compiled_re.search(os.path.basename(
                        member.name))):
                    found.append(member.name)

        return found

    def get_directories_re(
            self,
            directory_re,
            full_path=False,
            ignorecase=False):
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
                    if ((full_path and compiled_re.search(to_match)) or (
                            not full_path and compiled_re.search(
                                os.path.basename(to_match)))):
                        found.add(to_match)

        return list(found)

    @property
    def top_directory(self):
        """Return the name of the archive topmost directory."""
        if self.handle:
            return os.path.commonprefix(self.handle.getnames()).rstrip('/')

    @property
    def json_wheel_metadata(self):
        """Simple getter that get content of metadata.json file in .whl archive
        Returns:
            metadata from metadata.json or pydist.json in json format
        """
        for meta_file in ("metadata.json", "pydist.json"):
            try:
                return json.loads(self.get_content_of_file(meta_file))
            except TypeError as err:
                logger.warning(
                    'Could not extract metadata from {}.'
                    ' Error: {}'.format(meta_file, err))
        sys.exit(
            'Unable to extract package metadata from .whl archive. '
            'This might be caused by an old .whl format version. '
            'You may ask the upstream to upload fresh wheels created '
            'with wheel >= 0.17.0 or to upload an sdist as well to '
            'workaround this problem.')

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

        return {'modules': sorted(set(modules)),
                'scripts': sorted(set(scripts))}
