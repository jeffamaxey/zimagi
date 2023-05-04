from io import StringIO
from os import path

import os
import paramiko
import string
import random


class SSH(object):

    @classmethod
    def create_keypair(cls):
        key = paramiko.RSAKey.generate(4096)
        private_str = StringIO()
        key.write_private_key(private_str)
        return private_str.getvalue(), f"ssh-rsa {key.get_base64()}"

    @classmethod
    def create_password(cls, length = 32):
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(length))


    def __init__(self, hostname, username, password, key = None, callback = None, timeout = 30, port = 22, env = None):
        if not env:
            env = {}

        self.client = None
        self.sftp = None
        self.exec_wrapper = None
        self.exec_wrapper = None
        self.callback = None

        self.env = env
        self.hostname = hostname
        self.port = port
        self.timeout = timeout

        if hostname.find(":") >= 0:
            hostname, portstr = hostname.split(":")
            self.hostname = hostname
            self.port = int(portstr)

        self.username = username
        self.password = password
        self.key = None

        if key:
            self.key = paramiko.RSAKey.from_private_key(StringIO(key))

        self.connect()
        self.exec('id')
        self.callback = callback

    def __del__(self):
        self.close()


    def wrap_file(self, callback):
        self.file_wrapper = callback

    def wrap_exec(self, callback):
        self.exec_wrapper = callback


    def connect(self):
        if self.client:
            self.close()

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.key:
            try:
                self.client.connect(
                    self.hostname,
                    self.port,
                    self.username,
                    pkey = self.key,
                    look_for_keys = False,
                    allow_agent = False,
                    timeout = self.timeout
                )
            except Exception as e:
                if self.password:
                    self.client.connect(
                        self.hostname,
                        self.port,
                        self.username,
                        self.password,
                        timeout = self.timeout
                    )
                else:
                    raise e
        else:
            self.client.connect(
                self.hostname,
                self.port,
                self.username,
                self.password,
                timeout = self.timeout
            )

        self.sftp = self.client.open_sftp()

    def close(self):
        try:
            self.client.close()
            self.sftp.close()
        except:
            pass


    def download(self, remote_file, local_file, mode = None):

        def callback(remote_file, local_file, mode):
            tmp_file = "/tmp/dl.{}.zimagi".format(random.randint(1, 1000001))

            if path.isdir(local_file):
                remote_file_name = path.basename(remote_file)
                local_file = "{}/{}".format(local_file, remote_file_name)

            # Since we can't use sudo and sftp together we need to
            # jump through some hoops
            self.sudo("cp -f {} {}".format(remote_file, tmp_file))
            self.sudo("chmod 644 {}".format(tmp_file))

            self.sftp.get(tmp_file, local_file)
            self.sudo("rm -f {}".format(tmp_file))

            if mode:
                os.chmod(local_file, oct(int(str(mode), 8)))

        if self.file_wrapper and callable(self.file_wrapper):
            return self.file_wrapper(self, self._handle_file, callback, remote_file, local_file, mode)
        return self._handle_file(callback, remote_file, local_file, mode)

    def upload(self, local_file, remote_file, mode = None, owner = None, group = None):

        def callback(local_file, remote_file, mode, owner, group):
            tmp_file = "/tmp/ul.{}.zimagi".format(random.randint(1, 1000001))

            if path.isdir(remote_file):
                local_file_name = path.basename(local_file)
                remote_file = "{}/{}".format(remote_file, local_file_name)

            # Since we can't use sudo and sftp together we need to
            # jump through some hoops
            self.sftp.put(local_file, tmp_file)
            self.sudo("cp -f {} {}".format(tmp_file, remote_file))
            self.sudo("rm -f {}".format(tmp_file))

            if owner or group:
                if owner and group:
                    owner = "{}:{}".format(owner, group)
                elif group:
                    owner = ":{}".format(group)

                self.sudo("chown {} {}".format(owner, remote_file))

            if mode:
                self.sudo("chmod {} {}".format(oct(int(str(mode), 8))[2:], remote_file))

        if self.file_wrapper and callable(self.file_wrapper):
            return self.file_wrapper(self, self._handle_file, callback, local_file, remote_file, mode, owner, group)
        return self._handle_file(callback, local_file, remote_file, mode, owner, group)

    def _handle_file(self, callback, *args):
        callback(*args)


    def exec(self, command, *args, **options):
        if self.exec_wrapper and callable(self.exec_wrapper):
            return self.exec_wrapper(self, self._exec, command, args, options)
        return self._exec(command, args, options)

    def sudo(self, command, *args, **options):
        command = f"sudo -E -S -p '' {command}"
        return self.exec(command, *args, **options)

    def _exec(self, command, args, options):
        status = -1

        separator = options.pop('_separator', ' ')
        command = self._format_command(command, args, options, separator)
        is_sudo = command.startswith('sudo')

        env = [f"{variable}='{value}'" for variable, value in self.env.items()]
        env = " ".join(env) + ' '

        stdin, stdout, stderr = self.client.exec_command(f"{env}{command}".strip())

        if is_sudo and self.password:
            stdin.write(self.password + "\n")
            stdin.flush()

        if self.callback and callable(self.callback):
            self.callback(self, stdin, stdout, stderr)

        return stdout.channel.recv_exit_status()


    def _format_command(self, command, args, options, separator = ' '):
        components = [command]

        for arg in args:
            if arg[0] == '-':
                components.append(arg)
            else:
                components.append(f'{arg}')

        components.extend(f'{key}{separator}{value}' for key, value in options.items())
        return " ".join(components)
