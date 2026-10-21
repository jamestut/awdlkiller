#!/usr/bin/env python3

import sys
import os
import subprocess
import re

PLIST_NAME = 'jamestut.awdlkiller.plist'
PLIST_PATH = os.path.join('/Library/LaunchDaemons', PLIST_NAME)
SERVICE_TARGET = 'system/jamestut.awdlkiller'
LAUNCHCTL = '/bin/launchctl'
IFCONFIG = '/sbin/ifconfig'

def show_usage():
    print("awdl (status|on|off)")
    sys.exit(1)

def run_as_sudo():
    # Preserve the interpreter, including when invoked as `python3 manager.py`.
    os.execv('/usr/bin/sudo', [
        'sudo', sys.executable, os.path.abspath(__file__), *sys.argv[1:]
    ])

def root_check():
    if os.geteuid() != 0:
        run_as_sudo()

def run_command(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True)

def service_loaded():
    result = subprocess.run(
        [LAUNCHCTL, 'print', SERVICE_TARGET], capture_output=True, text=True
    )
    if result.returncode not in (0, 113):  # launchctl: service not found
        result.check_returncode()
    return result.returncode == 0

def stop_service():
    if service_loaded():
        run_command([LAUNCHCTL, 'bootout', SERVICE_TARGET])

def start_service():
    if not os.path.isfile(PLIST_PATH):
        raise FileNotFoundError(f'{PLIST_PATH} is missing; run the installer first.')
    run_command([LAUNCHCTL, 'enable', SERVICE_TARGET])
    if not service_loaded():
        run_command([LAUNCHCTL, 'bootstrap', 'system', PLIST_PATH])
    run_command([LAUNCHCTL, 'kickstart', SERVICE_TARGET])

def report_error(exc):
    if isinstance(exc, subprocess.CalledProcessError):
        detail = (exc.stderr or exc.stdout or '').strip()
        print(f"Command failed ({exc.returncode}): {' '.join(exc.cmd)}", file=sys.stderr)
        if detail:
            print(detail, file=sys.stderr)
    else:
        print(str(exc), file=sys.stderr)

def main():
    if len(sys.argv) != 2:
        show_usage()

    if sys.argv[1] == "status":
        po = run_command([IFCONFIG, 'awdl0'])
        flags = re.search(r'flags=[0-9a-fA-F]+<([^>]*)>', po.stdout)
        if flags is None:
            raise ValueError('Cannot read awdl0 interface flags from ifconfig output.')
        # IFF_UP controls administrative state; IFF_RUNNING indicates resources.
        running = 'UP' in flags.group(1).split(',')
        print(f'AWDL is {("running" if running else "inactive")}')
        return 0
    elif sys.argv[1] in {"on", "off"}:
        root_check()
        if sys.argv[1] == "off":
            # start the killer
            start_service()
        else:
            # Persist the choice across reboots, then stop the current instance.
            run_command([LAUNCHCTL, 'disable', SERVICE_TARGET])
            stop_service()
            run_command([IFCONFIG, 'awdl0', 'up'])
        return 0
    else:
        show_usage()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        report_error(exc)
        sys.exit(1)
