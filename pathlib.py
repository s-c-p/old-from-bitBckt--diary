import os
from collections import namedtuple

op = os.path

FilePointer = namedtuple("FilePointer", ["path_elements", "exists", "nature"])

class FilePath(object):
    """ abstract handler for filepaths """

    def __init__(self, strFilePath):
        # self.filePath = filePath.split(os.sep)
        self._parse(strFilePath)
        return

    def _parse(strFilePath):
        a = strFilePath.split(os.sep)
        b = op.isdir(strFilePath) or op.isfile(strFilePath)
        c = determineNature(strFilePath)
        self.file = FilePointer(a, b, c)
        return

    def getElem(index):
        if not type(index) is int:
            raise ValueError
        ans = self.file.path_elements[]
        ans = op.sep.join(ans)
        return ans