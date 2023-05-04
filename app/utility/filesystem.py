from contextlib import contextmanager

import os
import pathlib
import shutil
import threading
import oyaml


file_lock = threading.Lock()


def get_files(path):
    files = []

    if isinstance(path, (list, tuple)):
        path_str = os.path.join(*path)
        path = list(path)
    else:
        path_str = path
        path = [ path ]

    if os.path.isdir(path_str):
        for name in os.listdir(path_str):
            files.extend(get_files([ *path, name ]))
    else:
        files = [ path ]

    return files


def create_dir(dir_path, permissions = None):
    with file_lock:
        pathlib.Path(dir_path).mkdir(parents = True, exist_ok = True)

    if permissions is not None:
        if isinstance(permissions, str):
            permissions = int(permissions, 8)

        path_obj = pathlib.Path(dir_path)
        path_obj.chmod(permissions)

def remove_dir(dir_path, ignore_errors = True):
    with file_lock:
        shutil.rmtree(dir_path, ignore_errors = ignore_errors)


def load_file(file_path, binary = False):
    operation = 'rb' if binary else 'r'
    content = None

    if os.path.exists(file_path):
        with open(file_path, operation) as file:
            content = file.read()
    return content

def load_yaml(file_path):
    content = load_file(file_path)
    if content:
        content = oyaml.safe_load(content)
    return content

def save_file(file_path, content, binary = False, append = False, permissions = None):
    if append:
        operation = 'ab' if binary else 'a'
    else:
        operation = 'wb' if binary else 'w'

    with file_lock:
        pathlib.Path(os.path.dirname(file_path)).mkdir(parents = True, exist_ok = True)
        with open(file_path, operation) as file:
            file.write(content)

        if permissions is not None:
            if isinstance(permissions, str):
                permissions = int(permissions, 8)

            path_obj = pathlib.Path(file_path)
            path_obj.chmod(permissions)

def save_yaml(file_path, data, permissions = None):
    save_file(file_path, oyaml.dump(data), permissions = permissions)

def remove_file(file_path):
    with file_lock:
        os.remove(file_path)


@contextmanager
def filesystem_dir(base_path):
    yield FileSystem(base_path)


class FileSystem(object):

    def __init__(self, base_path, permissions = None):
        self.base_path = base_path
        self.permissions = permissions

        create_dir(self.base_path, permissions = self.permissions)


    def mkdir(self, directory):
        path = os.path.join(self.base_path, directory)
        create_dir(path, permissions = self.permissions)
        return path

    def listdir(self, directory = None):
        path = os.path.join(self.base_path, directory) if directory else self.base_path
        return os.listdir(path)


    def path(self, file_name, directory = None):
        if file_name.startswith(self.base_path):
            return file_name

        path = self.mkdir(directory) if directory else self.base_path
        return os.path.join(path, file_name)

    def exists(self, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        return bool(os.path.exists(path))


    def load(self, file_name, directory = None, binary = False):
        path = self.path(file_name, directory = directory)
        return load_file(path, binary) if os.path.exists(path) else None

    def save(self, content, file_name, directory = None, extension = None, binary = False, append = False, permissions = None):
        path = self.path(file_name, directory = directory)

        if extension:
            path = f"{path}.{extension}"

        save_file(path, content,
            binary = binary,
            append = append,
            permissions = permissions
        )
        return path

    def link(self, source_path, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if os.path.isfile(path) or os.path.islink(path):
            remove_file(path)

        with file_lock:
            os.symlink(source_path, path)
        return path

    def copy(self, source_path, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if os.path.isfile(path):
            remove_file(path)

        with file_lock:
            shutil.copy(source_path, path)
        return path

    def remove(self, file_name, directory = None):
        path = self.path(file_name, directory = directory)
        if path.startswith(self.base_path):
            if os.path.isdir(path):
                remove_dir(path)
            elif os.path.isfile(path):
                remove_file(path)

    def delete(self):
        remove_dir(self.base_path)
