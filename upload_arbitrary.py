import pyicloud
from pyicloud.exceptions import PyiCloudException, PyiCloudAPIResponseException, PyiCloudFailedLoginException, PyiCloudNoDevicesException, PyiCloudServiceNotActivatedException
import click
import dotenv
import itertools
import os
import pprint
import shutil
from pathlib import Path

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
        password = click.prompt('Enter password')

if os.getenv('TO_UPLOAD_PATH') is not None:
    local = os.getenv('TO_UPLOAD_PATH')
else:
    local = Path(click.prompt('Enter absolute path to local file'))

# get the absolute path from whatever is provided
if str(local).find('/'):
    if str(local.parent) == '~':
        local = local.expanduser()
else:
    local = local.resolve()

existing_item = None
overwrite_intended = False
to_upload_path = local

iCloud_client = pyicloud.PyiCloudService(user, password)
# check for existing session at default location /tmp/pyicloud/{hostname}/{appleidwith[@_.]stripped(e.g., emailexamplecom)}
try:
    iCloud_client._validate_token()
except (pyicloud.exceptions.PyiCloudAPIResponseException, pyicloud.exceptions.PyiCloudFailedLoginException) as e:
    print("new 2fa login required")
    verificationcode = click.prompt('Enter code that popped up on device!11')
    try:
        iCloud_client.validate_2fa_code(verificationcode)
    except Exception as e:
        raise e

class File_Tree_Node():
    def __init__(self, drive_node, parent=None):
        if isinstance(drive_node, File_Tree_Node):
            print('tried to instantiate existing node!')
            return None

        self.data = drive_node

        self.children = self.get_children()
        self.type = self.get_type()
        self.parent = parent

    def get_children(self):
        # assign parent attribute to child DriveNode objects so they may be instantiated as File_Tree_Node objects
        # classic tree-- child.parent = self
        # DriveNode.get_children() method returns list _children

        def _reducer(child):
            return {'child': child, 'parent': self}

        return [_reducer(x) for x in self.data.get_children()]

    def get_type(self):
        return self.data.type

    def get_child_folders(self):
        return (File_Tree_Node(x['child'], x['parent']) for x in self.children if x['child'].type == 'folder')
    
    def get_child_files(self):
        return (File_Tree_Node(x['child'], x['parent']) for x in self.children if x['child'].type == 'file')

    def get_child_nodes(self):
        return itertools.chain(self.get_child_folders(), self.get_child_files())

def build_file_tree(starting_node):
    if isinstance(starting_node, pyicloud.services.drive.DriveNode):
        root = File_Tree_Node(starting_node)
    else:
        root = File_Tree_Node(starting_node.data, parent=starting_node.parent)

    return root

def descend_file_tree(starting_node):
    if not isinstance(starting_node, File_Tree_Node):
        return

    for child in starting_node.get_child_folders():
        yield child
        for grandchild in descend_file_tree(child):
            yield grandchild

def formatter(file_tree_node):
    def _root(x):
        return x.data.name

    def _files(x):
        return [i.data.name for i in x.get_child_files()]

    def _folders(x):
        return [{'folder': i.data.name, 'contents': i.data.data['directChildrenCount']} for i in x.get_child_folders()]

    return({
        "Current Directory": _root(file_tree_node),
        "Files": _files(file_tree_node),
        "Folders": _folders(file_tree_node)
        })

dir = click.prompt(f'From\n{iCloud_client.drive.dir()}\nEnter the target directory, or type "ls [target_dir]" to expand')

if dir.split(' ')[0] == 'ls':
    child_dir = ' '.join(dir.split(' ')[1:])

    res = build_file_tree(iCloud_client.drive[child_dir])
    pprint.pprint(formatter(res), sort_dicts=False)

    dir = click.prompt('Select a folder, or press `enter` to use the current folder', default='')
    if dir == '':
        print('enter!')
        dir = res.data
    else:
        print(dir+'!')
        dir = res.data[dir]

def integrity_check(local_path, iCloud_dir, overwrite_intended=False, to_delete_file=None):
    checker_session = pyicloud.PyiCloudService(user,password)

    checker_session_node = checker_session.drive[iCloud_dir.name].get(local_path.name)

    if checker_session_node.type == 'file':
        if overwrite_intended == True:
            deleted_node = checker_session.drive.move_items_to_trash(
                to_delete_file.get('drivewsid'),
                to_delete_file.get('etag'),
                )
            return(checker_session_node, deleted_node)
        else:
            return(checker_session_node, {})

def upload_archive(local_path, iCloud_dir, existing_item=None, overwrite_intended=False, to_delete_file=None):
    if overwrite_intended == True:
        try:
            renamed_name=f"{'.'.join(existing_item.name.split('.')[:-1])}_deleteme.{existing_item.name.split('.')[-1]}"
            renamed_response = existing_item.rename(renamed_name)['items'][0]
            # logger.info(renamed_response)
            to_delete_file=renamed_response

        except Exception as e:
            raise e

    os.chdir(local_path.parents[0])
    with open(local_path.name, 'rb') as archive:
        try:
            iCloud_dir.upload(archive)
        except Exception as e:
            raise e

    # iCloud API does not return 
    return integrity_check(
        local_path,
        iCloud_dir,
        overwrite_intended,
        to_delete_file
        )

try:
    items = dir.dir()
    if local.name in items:
        existing_item = dir.get(local.name)

        if existing_item.type == 'file':
            overwrite_decision = click.prompt(
                f'Warning: file {local.name} already exists in /{dir.name}. \
                Would you like to overwrite it?\nEnter "Yes" or "No"'
                )

            if overwrite_decision.lower() in ['yes', 'y', 'overwrite']:
                overwrite_intended = True

            if overwrite_intended != True:
                new_file_name = click.prompt(f'Enter a new name for the file [old name: {local.name}]')
                to_upload_path = local.parent.joinpath(new_file_name)
                shutil.copy(local, to_upload_path)
         
    resp = upload_archive(
        local_path=to_upload_path,
        iCloud_dir=dir,
        existing_item=existing_item,
        overwrite_intended=overwrite_intended
        ) # do some logic about the existing file

except Exception as e:
    raise e

print(resp)