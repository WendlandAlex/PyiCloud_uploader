import pyicloud
from pyicloud.exceptions import PyiCloudException, PyiCloudAPIResponseException, PyiCloudFailedLoginException, PyiCloudNoDevicesException, PyiCloudServiceNotActivatedException
from pathlib import Path
import click
import dotenv
import os
import pprint


from Classes import File_Tree_Node, build_file_tree
from utils import authenticate_session, get_environment_variables, render_remote_DriveNode_path, render_tree, rename_file

def traverse_file_tree(File_Tree_Node_object):
    current_folder, formatted = build_file_tree(File_Tree_Node_object)

    available_folders = [i for i in current_folder.children if i.get('type') == 'folder']
    available_names = [list(i.keys())[-1] for i in available_folders]
    # check that the selected child folder is valid
    # for this we iterate over the metadata attributes exposed for this purpose in File_Tree_Node.children
    # if valid, use metadata key to get index of specific object in list of children, start a new search in that child
    # since python3 dicts are ordered, we trust that indices match between the 2 iterables

    dir = render_tree(formatted)

    if dir.split(' ')[0] == 'ls':
        dir = ' '.join(dir.split(' ')[1:])
        current_folder = available_folders[available_names.index(dir)].get('child')
        return traverse_file_tree(current_folder)

    if dir.lower() == 'here':
        return current_folder

    if dir.lower() == 'root':
        return traverse_file_tree(iCloud_client.drive.root)

    else:
        if dir in available_names:
            current_folder = File_Tree_Node(available_folders[available_names.index(dir)].get('child'))
            return current_folder

        else:
            print(f'\nFolder {dir} not present!\n')
            return traverse_file_tree(current_folder)


def integrity_check(local_path, DriveNode_object, is_root_node=False, overwrite_intended=False, to_delete_file=None):
    checker_session = pyicloud.PyiCloudService(user,password)
    checker_session_node = checker_session.drive.get_node_data(node_id=DriveNode_object.data.get("docwsid"))
    actually_existing_items = [f'{i.get("name")}.{i.get("extension")}' for i in checker_session_node.get("items")]

    if local_path.name in actually_existing_items:
        if overwrite_intended == True:
            deleted_node = checker_session.drive.move_items_to_trash(
                to_delete_file.get('drivewsid'),
                to_delete_file.get('etag'),
                )
            return local_path.name, deleted_node
        else:
            return local_path.name, {}


def upload_archive(local_path, DriveNode_object, is_root_node=False, existing_item=None, overwrite_intended=False, to_delete_file=None):
    if overwrite_intended == True and existing_item:
        try:
            renamed_name=f"{'.'.join(existing_item.name.split('.')[:-1])}_deleteme.{existing_item.name.split('.')[-1]}"
            to_delete_file = existing_item.rename(renamed_name)['items'][0]

        except Exception as e:
            raise e

    os.chdir(local_path.parents[0])
    with open(local_path.name, 'rb') as archive:
        try:
            DriveNode_object.upload(archive)
        except Exception as e:
            raise e

    # iCloud API does not return on success, so verify (before deleting, if applicable)
    return integrity_check(
        local_path,
        DriveNode_object,
        is_root_node,
        overwrite_intended,
        to_delete_file
        )


def generate_upload_params(DriveNode_object, local_file, selection_final=False):
    starting_dir = traverse_file_tree(DriveNode_object)
    if starting_dir.parent is None:
        is_root_node = True
    else:
        is_root_node = False
    to_upload_path = local_file
    existing_item = None
    overwrite_intended = False

    # File_Tree_Node wrapper class methods and attributes are only needed to traverse the filesystem
    # we now de-encapsulate the DriveNode class to access methods to upload, rename, or delete files
    starting_dir = starting_dir.drive_node

    try:
        items = starting_dir.dir()
        if local_file.name not in items:
            selection_final = True

        else:
            existing_item = starting_dir.get(local_file.name)

            if existing_item.type == 'file':
                overwrite_decision = click.prompt(
                    f'Warning: file {local_file.name} already exists in /{starting_dir.name}. \
                    Would you like to overwrite it?\nEnter "Yes" or "No"'
                    )

                if overwrite_decision.lower() in ['yes', 'y', 'overwrite']:
                    overwrite_intended = True
                    selection_final = True

                if overwrite_intended != True:
                    to_upload_path = rename_file(local_file, starting_dir)
                    selection_final = True

            else:
                print(f'ERROR: {existing_item.name} is a {existing_item.type}, not file')
                exit()

    except Exception as e:
        raise e

    return (to_upload_path,
        starting_dir,
        is_root_node,
        existing_item,
        overwrite_intended
        )


if __name__ == '__main__':
    dotenv.load_dotenv()
    user, password, local_file, remote_DriveNode_path, command_line_silent = get_environment_variables()

    # construct the absolute path to the local file from whatever is provided
    if str(local_file).find('/'):
        if str(local_file.parent) == '~':
            local_file = local_file.expanduser()
    else:
        local_file = local_file.resolve()
    if not local_file.is_file():
        print(f"ERROR: {local_file.name} does not exist at the specified path. Please check your spelling" )
        exit()

    # instantiate the iCloud client and check for an existing session on disk
    # if there is no usable session, initiate 2fa challenge
    iCloud_client = pyicloud.PyiCloudService(user, password)
    if not authenticate_session(iCloud_client):
        print(f"ERROR: authentication failed. Please check your credentials")
        exit()

    if command_line_silent:
        overwrite_intended = True
        # For unattended uploads, pass the names of folders in the path as a list in .env, or pass an empty list [] for root
        DriveNode_object, is_root_node = render_remote_DriveNode_path(iCloud_client, remote_DriveNode_path)
        try:
            existing_item = DriveNode_object.get(local_file.name)
        except IndexError:
            existing_item = None

        params = local_file, DriveNode_object, is_root_node, existing_item, overwrite_intended

    else:
        params = generate_upload_params(
            iCloud_client.drive.root,
            local_file,
            selection_final=False
            )

    uploaded, deleted = upload_archive(*params)

    print(
        'UPLOADED',
        pprint.pformat({'items': uploaded}),
        '\n',
        'DELETED',
        pprint.pformat(deleted),
        sep='\n'
    )
