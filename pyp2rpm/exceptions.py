class UnknownArchiveFormatException(BaseException):
    pass


class BadFilenameException(BaseException):
    pass


class NameNotSpecifiedException(BaseException):
    pass


class NoSuchPackageException(BaseException):
    pass


class NoSuchSourceException(BaseException):
    pass


class VirtualenvFailException(BaseException):
    pass


class ExtractionError(BaseException):
    pass


class MissingUrlException(BaseException):
    pass
