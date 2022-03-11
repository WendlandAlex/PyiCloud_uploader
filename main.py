import pyicloud
from pyicloud.exceptions import PyiCloudException, PyiCloudAPIResponseException, PyiCloudFailedLoginException, PyiCloudNoDevicesException, PyiCloudServiceNotActivatedException
import click
import dotenv
import datetime
import os
import pprint
import sys

from utils import authenticate_session

dotenv.load_dotenv()

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
        password = click.prompt('Enter Password')

iCloud_client = pyicloud.PyiCloudService(user, password)
verificationcode = click.prompt('Enter code that popped up on device!11')
try:
    iCloud_client.validate_2fa_code(verificationcode)
except Exception as e:
    raise e

pprint.pprint(iCloud_client.drive.dir())
if 'Backups' not in iCloud_client.drive.dir():
    sys.exit(1)

now = datetime.datetime.now().isoformat(timespec='seconds')

iCloud_client.drive['Backups'].mkdir(now)


with open('testbackup.json', 'rb') as archive:
    response = iCloud_client.drive['Backups'][now].upload(archive)

# confirm that the file uploaded
    assert iCloud_client.drive['Backups'][now]['testbackup.json'].type == 'file'
