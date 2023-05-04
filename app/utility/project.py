from contextlib import contextmanager

from django.conf import settings

from .environment import Environment
from .filesystem import FileSystem


@contextmanager
def project_dir(type, name):
    yield ProjectDir(type, name)


class ProjectDir(FileSystem):

    def __init__(self, type, name):
        self.type = type
        self.name = name
        super().__init__(
            f"{settings.LIB_DIR}/{self.type}/{Environment.get_active_env()}/{self.name}"
        )
