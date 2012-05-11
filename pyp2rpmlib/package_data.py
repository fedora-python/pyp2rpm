class PackageData(object):
    def __init__(self, name, version, md5 = None, pypi_url = None, pkg_type = None, local_file = None):
        self.name = name
        self.md5 = md5
        self.pypi_url = pypi_url
        self.pkg_type = pkg_type
        self.local_file = local_file
