# holodori-profile-export
Export your **hololive Dreams** game account into a portable **`.hdbest` profile** you can import on
[holodori.best](https://holodori.best) as a profile.

The profile file is an unencrypted gzipped json file.

## Usage (Release)
Download the {latest release link here} and run the file.

## Usage (Python)
Download the repository as a zip, then unzip it. Python 3.10+ is required (and should be in path).

```bash
pip install -r requirements.txt
python main.py # run the gui
python main.py --source <source> # run with CLI
```

It will create a `<user id>.hdbest` file. Upload that on holodori.best to import your account data (My Game Data -> Profiles -> click "Update" on a profile).

## Sources (`--source`)

| source | platform | how |
| --- | --- | --- |
| `steam` | Windows (Steam) | Finds and reads the game's credential from your installed Steam game. |
| `mitm` | Any platform | Intercept the game's network traffic using mitm to read the user data request's response. |
| `transfer` | Any platform | Logs in with your in-game transfer id + password; log back in on your device afterward. |
| `credential` | Any platform | Logs in with a raw account credential you already have (advanced). |

### `steam`
```
python main.py --source steam
```
Launch the game on this PC and log in at least once. It reads the newest credential file in `%USERPROFILE%\AppData\LocalLow\QualiArts, Inc_\hololive-Dreams`, to download user data.

### `transfer`
```
python main.py --source transfer --migration-id <ID> --password <PW>
```
Logs in with transfer credentials (logs you out on your real device), then downloads your user data.

You can log in again by simplying restarting the game on your real device.

### `credential` (advanced)
```
python main.py --source credential --credential <ACCOUNT CREDENTIAL>
```
If you've somehow extracted your game credential (NOT TRANSFER ID/PASSWORD), you can use it directly.

### `mitm` (advanced)
```
pip install mitmproxy
mitmdump -s holodori_profile_export/sources/mitm.py --set hdbest_out=.
```
Route the game client through mitmproxy (trust its CA), then launch/relaunch the game (load into the game past the title screen!). When the home
screen loads, the script decodes the snapshot and writes the `.hdbest`.

Basic knowledge on how to intercept network requests (or use a proxy) is required.

> [!TIP]
> The `--emudhra` option found on newer versions of mitmproxy can bypass the need for you to trust the CA.
> 
> It is unknown how much longer this will work though, as Unity has released a fix in newer Unity versions that no longer trusts the leaked certificates from eMudhra, and emails were sent to all Unity developers.

*Easy for non-Android devices. Requires a rooted Android device if used on Android.