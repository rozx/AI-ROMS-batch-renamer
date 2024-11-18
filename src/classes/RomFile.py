import hashlib
import os
import modules.utils as utilsModule



class RomFile:
    def __init__(self, path):
        self.path = path
        self.dir = os.path.dirname(path)
        self.originalFilename = os.path.basename(path)
        self.fileName = self.originalFilename
        self.md5 = utilsModule.getMD5HashFromFile(path)
        self.targetPath = os.path.join(self.dir, self.fileName)
        
        self.baseName, self.extName = os.path.splitext(self.fileName)


    def __str__(self) -> str:
        return self.fileName

    def baseName(self):
        return self.baseName
    
    def extName(self):
        return self.extName
    
    def updateFileName(self, newName):
        self.fileName = newName
        self.baseName, self.extName = os.path.splitext(self.fileName)
        self.targetPath = os.path.join(self.dir, self.fileName)

        return self.fileName