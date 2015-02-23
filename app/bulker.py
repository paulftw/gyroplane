import logging
import zipfile
import StringIO

class InMemoryZip(object):
    def __init__(self):
        # Create the in-memory file-like object
        self.in_memory_zip = StringIO.StringIO()

    def append(self, filename_in_zip, file_contents):
        '''Appends a file with name filename_in_zip and contents of 
        file_contents to the in-memory zip.'''
        # Get a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)

        # Write the file to the in-memory zip
        zf.writestr(filename_in_zip, file_contents)

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
            zfile.create_system = 0        

        return self

    def start_read(self):
        self.in_memory_zip.seek(0)

    def read(self, n=-1):
        '''Returns a string with the contents of the in-memory zip.'''
        return self.in_memory_zip.read(n)

    def writetofile(self, filename):
        '''Writes the in-memory zip to a file.'''
        f = file(filename, "w")
        f.write(self.read())
        f.close()


def generate_zip(files_dict):
    zipper = InMemoryZip()
    import base64

    for filename, fileobj in files_dict.items():
        content = fileobj['content']
        if fileobj['is_binary']:
            content = base64.standard_b64decode(content)
        zipper.append(filename, content)

    zipper.start_read()
    return zipper
