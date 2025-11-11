import os

from ai_rom_batch_renamer.modules import utils as utilsModule


class RomFile:
    def __init__(self, path):
        self.path = path
        self.dir = os.path.dirname(path)
        self.originalFilename = os.path.basename(path)
        self.fileName = self.originalFilename
        # Defer MD5 computation until explicitly needed to avoid heavy I/O on large files
        self._md5: str | None = None
        self.targetPath = os.path.join(self.dir, self.fileName)

        self.baseName, self.extName = os.path.splitext(self.fileName)

    def __str__(self) -> str:
        return self.fileName

    # def baseName(self):
    #     return self.baseName

    # def extName(self):
    #     return self.extName

    def updateFileName(self, newName):
        self.fileName = newName
        self.baseName, self.extName = os.path.splitext(self.fileName)
        self.targetPath = os.path.join(self.dir, self.fileName)

        return self.fileName

    @property
    def md5(self) -> str:
        """Lazily compute and cache the MD5 of the file in streaming mode.

        This avoids reading the entire file eagerly during construction, which
        is especially costly on slow media like SD cards.
        """
        if self._md5 is None:
            self._md5 = utilsModule.getMD5HashFromFile(self.path)
        return self._md5
