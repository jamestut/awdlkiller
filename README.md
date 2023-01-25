# awdlkiller

This app monitors for the macOS `awdl0` interface and **instantly** put that interface down the very moment it is detected up. `awdl0` is often the cause of ping spikes in macOS.

When this app is running, all macOS that depends on AWDL such as some Handoff and Continuity features (e.g. Universal Control, AirPlay, etc.) as well as AirDrop will not work.

## Installation

1. Copy the binary to `/usr/local/bin` (or any other preferred path).

2. Make the binary executable.

3. This app requires root: set the binary ownership to `root` and set the setuid bit (e.g. `chmod u+s awdlkiller`).

4. Copy `jamestut.awdlkiller.plist` to `/Library/LaunchDaemons`.



To set the service to start automatically, run:

```
sudo launchctl load -w /Library/LaunchDaemons/jamestut.awdlkiller.plist
```

Replace `load` with `unload` to disable the service.


