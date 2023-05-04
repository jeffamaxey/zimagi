from django.conf import settings

from utility.data import flatten

import os
import subprocess
import logging


logger = logging.getLogger(__name__)


class Shell(object):

    @classmethod
    def exec(cls, command_args, input = None, display = True, line_prefix = '', env = None, cwd = None, callback = None, sudo = False):
        if not env:
            env = {}

        shell_env = os.environ.copy()
        for variable, value in env.items():
            shell_env[variable] = value

        if sudo:
            if input:
                if isinstance(input, (list, tuple)):
                    input = [ settings.USER_PASSWORD, *flatten(input) ]
                else:
                    input = f"{settings.USER_PASSWORD}\n{input}"
            else:
                input = settings.USER_PASSWORD

            command_args = [ 'sudo', '-S', *flatten(command_args) ]

        process = subprocess.Popen(command_args,
                                   bufsize = 0,
                                   env = shell_env,
                                   cwd = cwd,
                                   stdin = subprocess.PIPE,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE)
        if input:
            if isinstance(input, (list, tuple)):
                input = "\n".join(input) + "\n"
            else:
                input = input + "\n"

            process.stdin.write(input.encode('utf-8'))
        try:
            if callback and callable(callback):
                callback(process, line_prefix, display = display)

            process.wait()
        finally:
            logger.debug(
                f"Terminating shell command {' '.join(command_args)} with status {process.returncode}"
            )
            process.terminate()

        return process.returncode == 0

    @classmethod
    def capture(cls, command_args, input = None, line_prefix = '', env = None, cwd = None):
        if not env:
            env = {}

        output = []

        def process(process, line_prefix, display):
            for line in process.stdout:
                line = line.decode('utf-8').strip('\n')
                output.append("{}{}".format(line_prefix, line))

        cls.exec(command_args,
            input = input,
            display = False,
            env = env,
            cwd = cwd,
            callback = process
        )
        return "\n".join(output).strip()
