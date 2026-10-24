# awdlkiller

This app monitors for the macOS `awdl0` interface and **instantly** put that interface down the very moment it is detected up. `awdl0` is often the cause of ping spikes in macOS.

When this app is running, all macOS that depends on AWDL such as some Handoff and Continuity features (e.g. Universal Control, AirPlay, etc.) as well as AirDrop will not work.

# Installation (Automatic)

Build the binary with `make awdlkiller`, then run `sudo python3 misc/installer.py`. The installer will do the following:

- Copy the `awdlkiller` to `/usr/local/bin`, setting it to be owned by `root:wheel` (no setuid; the LaunchDaemon already runs as root).
- Copy the `jamestut.awdlkiller.plist` to `/Library/LaunchDaemons` and activate automatic start.
- Copy the `manager.py` to `/usr/local/bin/awdl`, and setting it to be owned by `root:wheel`.

Rerun the installer to update changed files or repair permissions. It reloads the system LaunchDaemon after installing changes and reports launchctl failures. Installation enables the daemon, which disables AWDL.

## Note

- The installer refuses to install if `/usr/local/bin` (or any parent) is writable by a non-root user, e.g. on Intel Macs where Homebrew owns `/usr/local`. A root LaunchDaemon in such a directory lets that user replace the binary and gain root. Fix the ownership (`sudo chown root:wheel /usr/local/bin && sudo chmod go-w /usr/local/bin`) or change `BIN_TARGET_DIR` and the plist's `Program` path.
- Errors are logged to `/var/log/awdlkiller.log`.

- Both the installer and the manager script requires Python 3. Install Python 3 using `xcode-select --install`.
- The installer cannot do uninstallation at the moment. You have to reverse the above steps manually to uninstall.

# Installation (Manual)

1. Copy the binary to `/usr/local/bin` (or any other preferred path).

2. Make the binary executable (`sudo chmod +x awdlkiller`).

3. This app requires root.
   - The system LaunchDaemon already runs as root; setuid is not required for it.
   - To allow directly running the binary without `sudo`, set root ownership (`sudo chown root awdlkiller`) and the setuid bit (`sudo chmod u+s awdlkiller`). This lets any local user disable AWDL, so the automatic installer does not do this.

   - Make sure the directory holding the binary is not writable by non-root users.

4. Copy `jamestut.awdlkiller.plist` to `/Library/LaunchDaemons`.
   - If the path of `awdlkiller` is not in `/usr/local/bin`, please adjust contents of this plist accordingly.
   - Ensure that the `/Library/LaunchDaemons/jamestut.awdlkiller.plist` is owned by `root:wheel` and has the permission of `0644`.

5. (Optional) Copy `manager.py` to your `$PATH` for easy management. This file can be renamed to anything.
   - Note that `python3` is required. Install macOS' built-in Python using the `xcode-select --install` command.

To set the service to start automatically, run:

```
sudo launchctl enable system/jamestut.awdlkiller
sudo launchctl bootstrap system /Library/LaunchDaemons/jamestut.awdlkiller.plist
```

If the service is already loaded, skip `bootstrap`. To disable automatic startup and stop a loaded service, run:

```
sudo launchctl disable system/jamestut.awdlkiller
sudo launchctl bootout system/jamestut.awdlkiller
sudo ifconfig awdl0 up
```

The included `manager.py` script provides an easy way to enable and disable the awdlkiller. It does so via `launchctl`.
Use `awdl off` to start the killer and disable AWDL, `awdl on` to stop the killer and bring AWDL up, and `awdl status` to check the interface's administrative state. The on/off choice persists across reboots. The plist keeps the daemon running, retrying if it exits (including when `awdl0` is not yet available during boot).
