# prints # of lines of source code
import os
import sys

PY_EXTENSION = '.py'
py_files = []


# Recursively scan al subdirectories
def checkDirectory(start_directory):
    # file_name is a directory entry object
    for filepath in os.scandir(start_directory):
        if filepath.is_dir():
            checkDirectory(filepath.path)  # recursively scan subdirectories

        # Skip this file
        if filepath.name.startswith('linecheck'):
            continue

        if filepath.name.endswith(PY_EXTENSION):  # add src file to list
            py_files.append(filepath.path)


def countLines(files):
    count = 0

    for path in files:
        file = open(str(path), 'r')
        for item in enumerate(file):
            count += 1
        file.close()

    print('Total lines of code:', count)


checkDirectory('./')
countLines(py_files)
