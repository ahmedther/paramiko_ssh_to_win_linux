import os
import shutil
import paramiko
import time
import itertools
from datetime import datetime


class RemoteConnection:
    """
    paramiko and winrm are both Python libraries used for remote execution of commands on Windows servers, but they use different protocols for communication.

    paramiko uses the SSH protocol, which is commonly used for secure remote access and command execution on Linux servers, but can also be used on Windows servers.

    """

    def __init__(self, ip, username, password, os_type: str):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(ip, username=username, password=password)
        self.connection_time = time.perf_counter()
        self.os_type = os_type.lower()
        print(
            f"Connection With " + f" Linux {ip} Successfully Established"
            if self.os_type == "linux"
            else f" Windows {ip} Successfully Established"
        )

    def close_connection(self):
        self.ssh.close()
        closing_time = time.perf_counter()
        print(f"\n\n\n Total Connecntion Time : {closing_time - self.connection_time}")

    def copy_files_to_server(self, file_source, file_destination):
        # Get a list of files and directories in the local directory
        local_entries = os.listdir(file_source)

        # Get a list of files and directories in the remote directory
        dir_cmd = self.linux_or_windows_determiner("ls", "dir /b")
        stdin, stdout, stderr = self.ssh.exec_command(f"{dir_cmd} {file_destination}")
        remote_entries = stdout.read().decode().splitlines()

        for local_entry in local_entries:
            local_entry_path = os.path.join(file_source, local_entry)
            remote_entry_path = self.linux_or_windows_determiner(
                f"{file_destination}/{local_entry}",
                os.path.join(file_destination, local_entry),
            )

            if os.path.isfile(local_entry_path):
                local_mod_time = os.path.getmtime(local_entry_path)
                if local_entry not in remote_entries:
                    sftp = self.ssh.open_sftp()
                    sftp.put(local_entry_path, remote_entry_path)
                    print(f"Copying to {remote_entry_path}")
                    sftp.close()

                if local_entry in remote_entries:
                    if self.os_type == "linux":
                        stdin, stdout, stderr = self.run_ssh_command_on_server(
                            "stat -c %Y", remote_entry_path
                        )
                        remote_mod_time = int(stdout.read().decode().strip())

                    if self.os_type == "windows":
                        stdin, stdout, stderr = self.run_ssh_command_on_server(
                            f'for %I in ("{remote_entry_path}") do echo %~tI',
                            type=0,
                            remote_entry_path="",
                        )
                        remote_mod_time = self.epoch_working(stdout)

                    if local_mod_time > remote_mod_time:
                        sftp = self.ssh.open_sftp()
                        sftp.put(local_entry_path, remote_entry_path)
                        print(f"Overwriting to {remote_entry_path}")
                        sftp.close()

            if os.path.isdir(local_entry_path):
                self.run_ssh_command_on_server("mkdir", remote_entry_path)
                self.copy_files_to_server(local_entry_path, remote_entry_path)

        for remote_entry in remote_entries:
            remote_entry_path = self.linux_or_windows_determiner(
                f"{file_destination}/{remote_entry}",
                os.path.join(file_destination, remote_entry),
            )

            local_entry_path = os.path.join(file_source, remote_entry)
            if remote_entry not in local_entries:
                remove_cmd = self.linux_or_windows_determiner(
                    f'rm -rf "{remote_entry_path}"',
                    # f'del /q "{remote_entry_path}" && rd /s /q  "{remote_entry_path}"',
                    f'if exist "{remote_entry_path}" (if exist "{remote_entry_path}\*" (rd /s /q "{remote_entry_path}") else (del /q "{remote_entry_path}")) else (echo The directory "{remote_entry_path}" does not exist.)',
                )
                self.run_ssh_command_on_server(remove_cmd, type=1)
                print(f"Deleting {remote_entry_path}")

    def run_ssh_command_on_server(self, command, remote_entry_path=None, type=0):
        stdin, stdout, stderr = self.ssh.exec_command(
            f"{command} '{remote_entry_path}'"
        )
        if type == 1:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            stdout = f"\n\nStandard Output \t: {stdout.read().decode()}"
            stderr = f"Standard Error \t\t: {stderr.read().decode()}"

            if stdout != "\n\nStandard Output \t:":
                print(stdout)
            if stdout != "Standard Error \t\t:":
                print(stderr)
            return stdin, stdout, stderr
        return stdin, stdout, stderr

    def linux_restart_services(self):
        command_lists = [
            'echo -e "Don Z - Killing Begins\n"',
            "sudo -S pkill nginx",
            "sudo -S pkill apache2",
            "sudo -S pkill postgres",
            "sudo -S pkill RDBMS_Query_Reports_Portal_gunicorn.service",
            'echo -e "JoyBoy\n"',
            "sudo -S systemctl stop nginx",
            "sudo -S systemctl stop RDBMS_Query_Reports_Portal_gunicorn.service",
            'echo -e "\nRED X - Stating Services\n"',
            "sudo -S systemctl start nginx",
            "sudo -S systemctl start RDBMS_Query_Reports_Portal_gunicorn.service",
            'echo -e "Gonz Key\n"',
            "sudo -S service apache2 restart",
            "sudo -S service postgresql start",
            'echo -e "Deleting ALL files in web_exel_files"',
            "sudo -S rm -rf /home/ahmed/Desktop/AHMED/Django_Websites/reports_portal/Portal/web_excel_files/*",
            'echo -e "Dont have a good day! Have a great day!!!\n"',
        ]
        for commands in itertools.islice(command_lists, 0, len(command_lists)):
            self.run_ssh_command_on_server(
                f"echo 'ahmed' | {commands}",
                remote_entry_path=None,
                type=1,
            )

    def linux_or_windows_determiner(self, linux_command, windows_command):
        return linux_command if self.os_type == "linux" else windows_command

    def epoch_working(self, stdout):
        remote_mod_time = stdout.read().decode().strip().split()
        remote_mod_time = remote_mod_time[-3:-1]
        remote_mod_time = time.strptime(
            f"{remote_mod_time[0]} { remote_mod_time[1]}",
            "%d-%m-%Y %H:%M",
        )
        remote_mod_time = int(
            datetime.fromtimestamp(time.mktime(remote_mod_time)).timestamp()
        )
        return remote_mod_time


def report_portal_publish_windows(self, file_source, file_destination):
    if os.path.isdir(file_source):
        if not os.path.isdir(file_destination):
            os.makedirs(file_destination)
        for item in os.listdir(file_source):
            src = os.path.join(file_source, item)
            desti = os.path.join(file_destination, item)
            self.report_portal_publish_windows(src, desti)
    else:
        if (
            not os.path.exists(file_destination)
            or os.stat(file_source).st_mtime - os.stat(file_destination).st_mtime > 1
        ):
            shutil.copy2(file_source, file_destination)
            print(file_source)
