import click
import os
from pathlib import Path
import pyicloud
from pyicloud.exceptions import PyiCloudException, PyiCloudAPIResponseException, PyiCloudFailedLoginException, PyiCloudNoDevicesException, PyiCloudServiceNotActivatedException
import pprint
import shutil

def authenticate_session(PyiCloudService_object):
    # first try to load session data from the default location on disk
    # if no auth is present, client tries a blank session and gets
    # """
    # pyicloud.exceptions.PyiCloudAPIResponseException: Authentication required for Account. (421)
    # """
    # which we can handle just like a bad auth
    try:
        auth_attempt = PyiCloudService_object._validate_token()
        print(f"Authenticated as {PyiCloudService_object.data['dsInfo'].get('fullName')} ({PyiCloudService_object.data['dsInfo'].get('appleId')})")
        return True
    except (pyicloud.exceptions.PyiCloudAPIResponseException, pyicloud.exceptions.PyiCloudFailedLoginException) as e:
        print("new 2fa login required")
        verificationcode = click.prompt('Enter code that popped up on device!11')
        try:
            auth_attempt = PyiCloudService_object.validate_2fa_code(verificationcode)
            if auth_attempt == True:
                print(f"Authenticated as {PyiCloudService_object.data['dsInfo'].get('fullName')} ({PyiCloudService_object.data['dsInfo'].get('appleId')})")
                return True
            else:
                print(f"ERROR: failed to authenticate session for {PyiCloudService_object.data['dsInfo'].get('fullName')} ({PyiCloudService_object.data['dsInfo'].get('appleId')})")
                authenticate_session(PyiCloudService_object)
            
        except Exception as e:
            raise e


def get_environment_variables():
    if os.getenv('EMAIL') is not None:
        user = os.getenv('EMAIL')
    else:
        user = click.prompt('Enter AppleID')


    if os.getenv('PASSWORD') is not None:
        password = os.getenv('PASSWORD')
    else:
        if os.getenv('APP_SPECIFIC_PASSWORD') is not None:
            password = os.getenv('APP_SPECIFIC_PASSWORD')
        else:
            password = click.prompt('Enter password')


    if os.getenv('LOCAL_FILE') is not None:
        local_file = os.getenv('LOCAL_FILE')
    else:
        local_file = Path(click.prompt('Enter the path to a local file'))

    target_directory = os.getenv('TARGET_DIRECTORY', [])
    unattended = os.getenv('UNATTENDED', False)

    return user, password, local_file, target_directory, unattended


def render_target_directory(iCloud_client, target_directory):
    root = iCloud_client = iCloud_client.drive.root

    if isinstance(target_directory, str):
        target_directory = target_directory.rstrip('/').split('/')

    if len(target_directory) == 0:
        is_root_node = True
        return root, is_root_node
    else:
        for i in target_directory:
            root = root[i]

        is_root_node = False
        return root, is_root_node


def render_tree(node_attributes_dict):
    pprint.pprint(node_attributes_dict, sort_dicts=False)
    return click.prompt(f'\n  [ ] You are in /{node_attributes_dict.get("Current Directory")} [ ]\n      \n[1] type the name of a child folder, \n[2] type "ls <target_dir>" to expand, \n[3] type "here" to select the current folder, \n[4] type "root" to return to the top \n\n  [ ]')


def rename_file(Path_object, DriveNode_object):
    new_file_name = click.prompt(f'Enter a new name for the file [old name: {Path_object.name}]')
    to_upload_path = Path_object.parent.joinpath(new_file_name)
    try:
        shutil.copy(Path_object, to_upload_path)
    except shutil.SameFileError:
        print(f'A file named {to_upload_path} exists in local directory! Please enter a unique filename')
        rename_file(Path_object, DriveNode_object)
    
    # use the built-in _children property to avoid having to make duplicate network calls
    named = [i.name for i in DriveNode_object._children]
    if to_upload_path.name in named:
        print(f'A file named {to_upload_path} exists in /{DriveNode_object.name}! Please enter a unique filename')
        rename_file(Path_object, DriveNode_object)

    return to_upload_path
