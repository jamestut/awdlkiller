#!/usr/bin/env python3

import sys
import os
import subprocess

PLIST_NAME = 'jamestut.awdlkiller.plist'

def show_usage():
    print("awdl (status|on|off)")
    sys.exit(1)

def run_as_sudo():
    argv = list(sys.argv)
    argv.insert(0, 'sudo')
    os.execvp('sudo', argv)

def root_check():
    if os.getuid() != 0:
        run_as_sudo()
        return 1

def main():
    if len(sys.argv) != 2:
        show_usage()

    if sys.argv[1] == "status":
        po = subprocess.run(['ifconfig', 'awdl0'], capture_output=True)
        po_out = po.stdout.split(b'\n', maxsplit=2)
        running = b'RUNNING' in po_out[0]
        print(f'AWDL is {("running" if running else "inactive")}')
        return 0
    elif sys.argv[1] in {"on", "off"}:
        root_check()
        os.chdir('/Library/LaunchDaemons')
        if sys.argv[1] == "off":
            # start the killer
            cmds = [['launchctl', 'load', '-w', PLIST_NAME]]
        else:
            cmds = [
                ['launchctl', 'unload', PLIST_NAME],
                ['ifconfig', 'awdl0', 'up']
            ]
        for cmd in cmds:
            subprocess.run(cmd, capture_output=True, check=True)
    else:
        show_usage()

if __name__ == "__main__":
    sys.exit(main())
