#!/usr/bin/env python3
import argparse
import sys
import os
import stat
import shutil
import subprocess
import filecmp
import tempfile
from os import path

from manager import report_error, service_loaded, start_service, stop_service

BIN_TARGET_DIR = '/usr/local/bin'
SOURCE_DIR = path.dirname(path.abspath(__file__))

def main():
    todolist = []

    ap = argparse.ArgumentParser(description='Install awdlkiller and its manager to the system.')
    ap.add_argument('--force', action='store_true',
        help='Force install even if everything seems to be in place.')
    args = ap.parse_args()

    # root check
    if os.geteuid() != 0:
        print("Please run this installer as root.")
        return 1

    for todo in (
        AwdlKillerDaemon,
        AwdlManager,
        LaunchDaemonEntry,
    ):
        if args.force or not todo.check():
            todolist.append(todo)

    # A correctly installed plist may still be unloaded (or disabled).
    if not service_loaded() and LaunchDaemonEntry not in todolist:
        todolist.append(LaunchDaemonEntry)

    if not todolist:
        print("awdlkiller seems to be installed. Nothing to be done.")
        return 0

    # Check every required source before interrupting the existing service.
    for todo in todolist:
        if not path.isfile(todo.SOURCE_PATH):
            raise FileNotFoundError(
                f'{todo.SOURCE_PATH} is missing; build awdlkiller before installing.'
            )

    # prompt user of the actions that we're going to take
    print("This installer will take the following action:")
    for todo in todolist:
        print(f' - {todo.install_desc}')
    print(' - Reload and enable the system LaunchDaemon (disables AWDL).')
    answer = input("Enter Y to continue or any other key to cancel: ")
    if not (answer in ('Y', 'y')):
        print("Installation aborted.")
        return 1

    # continue with the install
    stop_service()
    for todo in todolist:
        todo.do_install()
    start_service()
    print("Installation finished!")
    return 0

def generate_mod(suid, exec):
    fmod = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR
    if suid:
        fmod |= stat.S_ISUID
    if exec:
        fmod |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    return fmod

def check_permission(filename, *, fmod):
    try:
        s = os.lstat(filename)
    except OSError:
        return False

    is_root_owned = all(i == 0 for i in (s.st_uid, s.st_gid))
    is_mode_ok = stat.S_IMODE(s.st_mode) == fmod
    return stat.S_ISREG(s.st_mode) and is_root_owned and is_mode_ok

class InstallerBase:
    @classmethod
    def check(cls):
        return (
            check_permission(cls.TARGET_PATH, fmod=cls.FMOD)
            and filecmp.cmp(cls.SOURCE_PATH, cls.TARGET_PATH, shallow=False)
        )

    @classmethod
    def do_copyfile_setperm(cls, srcpath, targetpath, fmod):
        print(f"Copying '{srcpath}' to '{targetpath}' ...")
        # Stage alongside the destination: replace atomically and never follow
        # a destination symlink or overwrite a running executable in place.
        fd, staged = tempfile.mkstemp(prefix='.awdlkiller-', dir=path.dirname(targetpath))
        try:
            with os.fdopen(fd, 'wb') as target, open(srcpath, 'rb') as source:
                shutil.copyfileobj(source, target)
                target.flush()
                os.fchown(target.fileno(), 0, 0)
                os.fchmod(target.fileno(), fmod)
            os.replace(staged, targetpath)
        finally:
            if path.exists(staged):
                os.unlink(staged)

    @classmethod
    def do_mkdir_localbin(cls):
        os.makedirs(BIN_TARGET_DIR, exist_ok=True)

class AwdlKillerDaemon(InstallerBase):
    install_desc = "Install 'awdlkiller' to '/usr/local/bin' and set root setuid."

    AWDLKILLER_NAME = 'awdlkiller'
    AWDLKILLER_TARGET_PATH = path.join(BIN_TARGET_DIR, AWDLKILLER_NAME)
    TARGET_PATH = AWDLKILLER_TARGET_PATH
    SOURCE_PATH = path.join(SOURCE_DIR, '..', AWDLKILLER_NAME)
    FMOD = generate_mod(suid=True, exec=True)

    @classmethod
    def do_install(cls):
        print("Installing awdlkiller ...")
        super().do_mkdir_localbin()
        super().do_copyfile_setperm(cls.SOURCE_PATH, cls.TARGET_PATH, cls.FMOD)

class AwdlManager(InstallerBase):
    install_desc = "Install 'manager.py' to '/usr/local/bin/awdl'."

    AWDLMGR_SRC_NAME = 'manager.py'
    AWDLMGR_NAME = 'awdl'
    AWDLMGR_TARGET_PATH = path.join(BIN_TARGET_DIR, AWDLMGR_NAME)
    TARGET_PATH = AWDLMGR_TARGET_PATH
    SOURCE_PATH = path.join(SOURCE_DIR, AWDLMGR_SRC_NAME)
    FMOD = generate_mod(suid=False, exec=True)

    @classmethod
    def do_install(cls):
        print("Installing awdl manager ...")
        super().do_mkdir_localbin()
        super().do_copyfile_setperm(cls.SOURCE_PATH, cls.TARGET_PATH, cls.FMOD)

class LaunchDaemonEntry(InstallerBase):
    install_desc = "Install 'jamestut.awdlkiller.plist' to '/Library/LaunchDaemons'."

    LAUNCHD_NAME = 'jamestut.awdlkiller.plist'
    LAUNCHD_TARGET_PATH = path.join('/Library/LaunchDaemons', LAUNCHD_NAME)
    TARGET_PATH = LAUNCHD_TARGET_PATH
    SOURCE_PATH = path.join(SOURCE_DIR, LAUNCHD_NAME)
    FMOD = generate_mod(suid=False, exec=False)

    @classmethod
    def do_install(cls):
        print("Installing awdlkiller auto start ...")
        os.makedirs(path.dirname(cls.TARGET_PATH), exist_ok=True)
        super().do_copyfile_setperm(cls.SOURCE_PATH, cls.TARGET_PATH, cls.FMOD)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, subprocess.CalledProcessError) as exc:
        report_error(exc)
        sys.exit(1)
