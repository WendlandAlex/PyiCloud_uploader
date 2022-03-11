import click
import os
from pathlib import Path
import pyicloud
from pyicloud.exceptions import PyiCloudException, PyiCloudAPIResponseException, PyiCloudFailedLoginException, PyiCloudNoDevicesException, PyiCloudServiceNotActivatedException

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

    return user, password