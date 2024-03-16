# awdlkiller

This app monitors for the macOS `awdl0` interface and **instantly** put that interface down the very moment it is detected up. `awdl0` is often the cause of ping spikes in macOS.

When this app is running, all macOS that depends on AWDL such as some Handoff and Continuity features (e.g. Universal Control, AirPlay, etc.) as well as AirDrop will not work.

# Installation (Automatic)

Run the included `installer.py` in the `misc` folder. The installer will do the following:

- Copy the `awdlkiller` to `/usr/local/bin`, setting it to be owned by `root:wheel`, and assigns setuid flag to it.
- Copy the `jamestut.awdlkiller.plist` to `/Library/LaunchDaemons` and activate automatic start.
- Copy the `manager.py` to `/usr/local/bin/awdl`, and setting it to be owned by `root:wheel`.

## Note

- Both the installer and the manager script requires Python 3. Install Python 3 using `xcode-select --install`.
- The installer cannot do uninstallation at the moment. You have to reverse the above steps manually to uninstall.

# Installation (Manual)

1. Copy the binary to `/usr/local/bin` (or any other preferred path).

2. Make the binary executable (`sudo chmod +x awdlkiller`).

3. This app requires root.
   - Set the binary ownership to `root` (`sudo chown root awdlkiller`).
   - Set the setuid bit (`sudo chmod u+s awdlkiller`).

4. Copy `jamestut.awdlkiller.plist` to `/Library/LaunchDaemons`.
   - If the path of `awdlkiller` is not in `/usr/local/bin`, please adjust contents of this plist accordingly.
   - Ensure that the `/Library/LaunchDaemons/jamestut.awdlkiller.plist` is owned by `root:wheel` and has the permission of `0644`.

5. (Optional) Copy `manager.py` to your `$PATH` for easy management. This file can be renamed to anything.
   - Note that `python3` is required. Install macOS' built-in Python using the `xcode-select --install` command.

To set the service to start automatically, run:

```
sudo launchctl load -w /Library/LaunchDaemons/jamestut.awdlkiller.plist
```

Replace `load` with `unload` to disable the service.

The included `manager.py` script provides an easy way to enable and disable the awdlkiller. It does so via `launchctl`.
