# Usage
## Mandatory setup
There is currently a bug in the pyiCloud module that fails to load one of the attributes returned by the iCloud API into the 'Drive' service class. Until the open PR at https://github.com/picklepete/pyicloud/pull/359 is merged, run `setup.sh` to create a virtual environment, install the module, and apply a patch. Then run `source bin/activate` to enter the virtual environment in your shell.

## Main command
Run `python3 PyiCloud_uploader.py` in the virtual environment to enter an interactive prompt. If you already know your remote filesystem structure, feel free to provide paths to source and destination files in a `.env` file.

## Environment Variables
```EMAIL ```
the iCloud account

```PASSWORD ``` or ```APP_SPECIFIC_PASSWORD```


```LOCAL_FILE ```
filename of the source file you want to upload. This may be either an absolute path or relative to the directory where the script is invoked

```UNATTENDED (boolean) ```
Optionally, disable interactive CLI input

```TARGET_DIRECTORY (list|str)```
If in unattended mode, provide the path to a subdirectory where the file at LOCAL_FILE will be uploaded. This may be either a `/` separated string, or a list of directory names