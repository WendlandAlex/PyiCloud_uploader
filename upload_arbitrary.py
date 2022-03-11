import pyicloud
from pyicloud.exceptions import PyiCloudException, PyiCloudAPIResponseException, PyiCloudFailedLoginException, PyiCloudNoDevicesException, PyiCloudServiceNotActivatedException
import click
import dotenv
import os
import pprint


from Classes import File_Tree_Node, build_file_tree, descend_file_tree, formatter
from utils import get_environment_variables, authenticate_session
from commandline import select_file, rename_file, traverse_file_tree
dotenv.load_dotenv()

user, password = get_environment_variables()
iCloud_client = pyicloud.PyiCloudService(user, password)

if not authenticate_session(iCloud_client):
    os.abort

local = select_file()

def navigate(DriveNode_object):
    dir = click.prompt(f'From\n{DriveNode_object.dir()}\nEnter the target directory, or type "ls [target_dir]" to expand')

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
            print(DriveNode_object[dir])
            # print([i for i in descend_file_tree(res.data[dir])])
            # dir = res.data[dir]
            navigate(DriveNode_object[dir])

    return dir

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

    # iCloud API does not return on success, so verify (before deleting, if applicable)
    return integrity_check(
        local_path,
        iCloud_dir,
        overwrite_intended,
        to_delete_file
        )

try:
    starting_dir = navigate(iCloud_client.drive)

    items = starting_dir.dir()
    overwrite_intended = False
    existing_item=None
    to_upload_path = local

    if local.name in items:
        existing_item = starting_dir.get(local.name)

        if existing_item.type == 'file':
            overwrite_decision = click.prompt(
                f'Warning: file {local.name} already exists in /{starting_dir.name}. \
                Would you like to overwrite it?\nEnter "Yes" or "No"'
                )

            if overwrite_decision.lower() in ['yes', 'y', 'overwrite']:
                overwrite_intended = True

            if overwrite_intended != True:
                to_upload_path = rename_file(local, starting_dir)

        else:
            print(f'ERROR: {existing_item.name} is a {existing_item.type}, not file')

    uploaded, deleted = upload_archive(
        local_path=to_upload_path,
        iCloud_dir=starting_dir,
        existing_item=existing_item,
        overwrite_intended=overwrite_intended
        ) # do some logic about the existing file

except Exception as e:
    raise e

print(
    'UPLOADED',
    pprint.pformat(uploaded.data),
    '\n,',
    'DELETED',
    pprint.pformat(deleted),sep='\n')
