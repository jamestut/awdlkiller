#!/usr/bin/env python3
import argparse
import sys
import os
import stat
import shutil
import subprocess
from os import path

BIN_TARGET_DIR = '/usr/local/bin'

def main():
    # change to script's directory
    dirtoch, _ = path.split(sys.argv[0])
    if dirtoch:
        os.chdir(dirtoch)

    todolist = []

    ap = argparse.ArgumentParser(description='Install awdlkiller and its manager to the system.')
    ap.add_argument('--force', action='store_true',
        help='Force install even if everything seems to be in place.')
    args = ap.parse_args()

    # root check
    if os.getuid() != 0:
        print("Please run this installer as root.")
        return 1

    for todo in (
        AwdlKillerDaemon,
        AwdlManager,
        LaunchDaemonEntry,
    ):
        if args.force or not todo.check():
            todolist.append(todo)

    if not todolist:
        print("awdlkiller seems to be installed. Nothing to be done.")
        return 0

    # prompt user of the actions that we're going to take
    print("This installer will take the following action:")
    for todo in todolist:
        print(f' - {todo.install_desc}')
    answer = input("Enter Y to continue or any other key to cancel: ")
    if not (answer in ('Y', 'y')):
        print("Installation aborted.")
        return 1

    # continue with the install
    for todo in todolist:
        todo.do_install()
    print("Installation finished!")

def generate_mod(suid, exec):
    fmod = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR
    if suid:
        fmod |= stat.S_ISUID
    if exec:
        fmod |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    return fmod

def check_permission(filename, *, fmod):
    try:
        s = os.stat(filename)
    except:
        return False

    is_root_owned = all(i == 0 for i in (s.st_uid, s.st_gid))
    is_acl_ok = (s.st_mode & fmod) == fmod
    return is_root_owned and is_acl_ok

class InstallerBase:
    @classmethod
    def do_copyfile_setperm(cls, srcpath, targetpath, fmod):
        print(f"Copying '{srcpath}' to '{targetpath}' ...")
        shutil.copyfile(srcpath, targetpath)
        print(f"Setting permissions to '{targetpath}' ...")
        os.chown(targetpath, 0, 0)
        os.chmod(targetpath, fmod)

    @classmethod
    def do_mkdir_localbin(cls):
        os.makedirs('/usr/local/bin', exist_ok=True)

class AwdlKillerDaemon(InstallerBase):
    install_desc = "Install 'awdlkiller' to '/usr/local/bin' and set root setuid."

    AWDLKILLER_NAME = 'awdlkiller'
    AWDLKILLER_TARGET_PATH = path.join(BIN_TARGET_DIR, AWDLKILLER_NAME)
    FMOD = generate_mod(suid=True, exec=True)

    @classmethod
    def check(cls):
        return check_permission(cls.AWDLKILLER_TARGET_PATH, fmod=cls.FMOD)

    @classmethod
    def do_install(cls):
        print("Installing awdlkiller ...")
        super().do_mkdir_localbin()
        super().do_copyfile_setperm(f'../{cls.AWDLKILLER_NAME}', cls.AWDLKILLER_TARGET_PATH, cls.FMOD)

class AwdlManager(InstallerBase):
    install_desc = "Install 'manager.py' to '/usr/local/bin/awdl'."

    AWDLMGR_SRC_NAME = 'manager.py'
    AWDLMGR_NAME = 'awdl'
    AWDLMGR_TARGET_PATH = path.join(BIN_TARGET_DIR, AWDLMGR_NAME)
    FMOD = generate_mod(suid=False, exec=True)

    @classmethod
    def check(cls):
        return check_permission(cls.AWDLMGR_TARGET_PATH, fmod=cls.FMOD)

    @classmethod
    def do_install(cls):
        print("Installing awdl manager ...")
        super().do_mkdir_localbin()
        super().do_copyfile_setperm(cls.AWDLMGR_SRC_NAME, cls.AWDLMGR_TARGET_PATH, cls.FMOD)

class LaunchDaemonEntry(InstallerBase):
    install_desc = "Install 'jamestut.awdlkiller.plist' to '/Library/LaunchDaemon' and activate autostart."

    LAUNCHD_NAME = 'jamestut.awdlkiller.plist'
    LAUNCHD_TARGET_PATH = path.join('/Library/LaunchDaemons', LAUNCHD_NAME)
    FMOD = generate_mod(suid=False, exec=False)

    @classmethod
    def check(cls):
        return check_permission(cls.LAUNCHD_TARGET_PATH, fmod=cls.FMOD)

    @classmethod
    def do_install(cls):
        print("Installing awdlkiller auto start ...")
        super().do_copyfile_setperm(cls.LAUNCHD_NAME, cls.LAUNCHD_TARGET_PATH, cls.FMOD)
        subprocess.run(['launchctl', 'load', '-w', cls.LAUNCHD_TARGET_PATH])

if __name__ == "__main__":
    sys.exit(main())
