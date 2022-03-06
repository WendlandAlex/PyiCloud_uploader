import pyicloud
from pyicloud.exceptions import PyiCloudException, PyiCloudAPIResponseException, PyiCloudFailedLoginException, PyiCloudNoDevicesException, PyiCloudServiceNotActivatedException
import click
import dotenv
import itertools
import os
import pprint
import shutil
import sys
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
        password = click.prompt('Enter Password')

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


class File_Tree():
    def __init__(self, root_node, child_nodes: list=[]):
        # prepare a list to append all child nodes to when called
        self.root_node = root_node
        self.child_nodes = child_nodes
        self.tree_list = [self]

    def insert_node(self, node):
        self.child_nodes.append(File_Tree(node))

    def get_all_children(self):
        try:
            for i in self.child_nodes:
                print(i)
        except Exception as e:
            raise e

    def get_children(self):
        return self.child_nodes

    def add_node(self, child, parent):
        # top-down
        # print(self.lineage)
        # node = Node(child)
        print(parent)
        if parent in self.child_nodes:
            parent.add_node(child, parent)
            # insert into linked list at this index + 1
        else:
            # insert at the level below the root
            # self.child_nodes.append(child)
            self.child_nodes.append(child)

    def print_nodes(self):
        pprint.pprint(self.tree_list)

    def __str__(self):
        return f'{self.child_nodes}'

    def __repr__(self):
        return f'<{type(self).__name__}: {str(self.child_nodes)}>'

class File_Tree_Node():
    def __init__(self, drive_node, parent=None):
        if isinstance(drive_node, File_Tree_Node):
            print('tried to instantiate existing node!')
            return None

        self.data = drive_node
        """
        Data Model:

        ({'dateCreated': '2022-02-13T05:00:20Z', 'drivewsid': 'FOLDER::com.apple.CloudDocs::FAC24BE2-7855-4851-904D-933D85DE2438', 
        'docwsid': 'FAC24BE2-7855-4851-904D-933D85DE2438', 'zone': 'com.apple.CloudDocs', 'name': 'Backups',
        'parentId': 'FOLDER::com.apple.CloudDocs::root', 'isChainedToParent': True, 'etag': 'kfg',
        'type': 'FOLDER', 'assetQuota': 128, 'fileCount': 4, 'shareCount': 0, 
        'shareAliasCount': 0, 'directChildrenCount': 5}, None)
        """

        self.children = self.get_children()
        self.type = self.get_type()
        self.parent = parent

    def get_children(self):
        # assign parent attribute to child DriveNode objects so they may be instantiated as File_Tree_Node objects
        # classic tree-- child.parent = self
        # DriveNode.get_children() returns list _children

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

    print(type(root))
    print(len(root.children))
    # print(root.child_files, root.child_folders)

    return root

def descend_file_tree(starting_node):
    if not isinstance(starting_node, File_Tree_Node):
        # return
        sys.exit('not class instance')

    for child in starting_node.get_child_folders():
        yield child
        for grandchild in descend_file_tree(child):
            yield grandchild

    # def __init__(self, drive_node, file_tree, parent=None, child_folders: list=[]):
    #     print(type(self),type(drive_node), type(parent))
    #     if parent is None: parent = file_tree
    #     self.file_tree = file_tree
    #     self.parent = parent
    #     self.drive_node = drive_node
    #     self.drive_node.get_children()
    #     # print.self.drive_node.data
    #     """
    #     ({'dateCreated': '2022-02-13T05:00:20Z', 'drivewsid': 'FOLDER::com.apple.CloudDocs::FAC24BE2-7855-4851-904D-933D85DE2438', 
    #     'docwsid': 'FAC24BE2-7855-4851-904D-933D85DE2438', 'zone': 'com.apple.CloudDocs', 'name': 'Backups',
    #     'parentId': 'FOLDER::com.apple.CloudDocs::root', 'isChainedToParent': True, 'etag': 'kfg',
    #     'type': 'FOLDER', 'assetQuota': 128, 'fileCount': 4, 'shareCount': 0, 
    #     'shareAliasCount': 0, 'directChildrenCount': 5}, None)
    #     """
    #     self.child_files = []
    #     self.child_folders = child_folders
    #     self.parent.insert_node(self)
    #     for item in self.drive_node._children:
    #         if item.type == 'folder':
    #             print(item)
    #             self.parent.insert_node(item)            


    # def get_children(self):
    #     pprint.pprint(self.drive_node._children)        
    #     for item in self.drive_node._children:
    #         print(item)
    #         if item.type == 'folder':
    #             print(item.data)
    #             self.child_folders.append(item)
    #             self.parent.insert_node(item)
    #         elif item.type == 'file':
    #             print(item.data)
    #             self.child_files.append(item)

    # def print_children(self):
    #     return {
    #         'files': self.child_files,
    #         'folders': self.child_folders
    #     }

    # def __str__(self):
    #     # return f"{type(self).__name__}"
    #     return f'{self.data[0].get("name")}'
    # def __repr__(self):
    #     return f'<{type(self).__name__}: {str(self)}>'

# TODO: walk directories
def one_way_descent(session, cwd):
    found = False
    while found != True:
        session = session[cwd]
        # print(session.data) # debug confirm that the parent is changing
        current = {
                'parent': "",
                'folder': [],
                'file': [],
                'levels': 0
            }
        for i in session.get_children():
            # print(i.type)
            current['levels'] += 1
            if i.type == 'folder':
                current['folder'].append(i)
                root_session.addNode(i)
            elif i.type == 'file':
                current['file'].append(i)
                root_session.addNode(i)

            for y in current['folder']:
                pass

        print(f"Files in this folder:\n\t{[y.name for y in current['file']]}\nDirectories in this folder:\n\t{[y.name for y in current['folder']]}\nType 'this' to select the current folder or type 'ls <folder>' to descend")
        cwd_old = cwd
        print(File_Tree)
        cwd = click.prompt("Enter <this|ls folder name>")
        if cwd.split(' ')[0] == 'ls':
            cwd = ' '.join(cwd.split(' ')[1:])
            one_way_descent(session, cwd)
        elif cwd == 'this':
            session = pyicloud.services.drive.DriveNode(conn=session.connection,data=session.data)
            # print(type(session))
        else:
            # accept the typed dir name
            session = session[cwd]
            session = pyicloud.services.drive.DriveNode(conn=session.connection,data=session.data)
        found = True
    return (session)

dir = click.prompt(f'From\n{iCloud_client.drive.dir()}\nEnter the target directory, or type "ls [target_dir]" to expand')


if dir.split(' ')[0] == 'ls':
    child_dir = ' '.join(dir.split(' ')[1:])
    # file_tree = File_Tree(iCloud_client.drive)
    # root_session = Node(iCloud_client.drive[child_dir], file_tree=file_tree)
    # for i in file_tree.child_nodes:
        # print(str(i))

    res = build_file_tree(iCloud_client.drive[child_dir])
    # for i in res.get_child_folders():
        # print(f'{i.data.name}={i} {i.child_folders}')
    # for i in res.get_child_files():
        # print(f'{i.data.name}={i}')

    for i in res.get_child_folders():
        for y in i.get_child_folders():
            print(y.data.name)

    def reducer(x):
        return {'name': x.data.name, 'self': x, 'parent': x.parent, 'type': x.data.type}

    # print(f'generators\n\n{[reducer(x) for x in res.get_child_nodes()]}')

    pprint.pprint(reducer(res))

    pprint.pprint([reducer(x) for x in res.get_child_files()])

    # print(descend_file_tree(res))
    pprint.pprint([reducer(x) for x in descend_file_tree(res)])

    # file_tree.print_nodes()
    # file_tree.get_all_children()
    # file_tree.print_nodes()
    # for i in root_session.get_children():
    #     root_session.add_node(i)
    # file_tree = one_way_descent(iCloud_client.drive, child_dir)
    # file_tree.get_children()
    # root_session.get_child_folders(file_tree)
    # pprint.pprint(root_session.lineage)
    # pprint.pprint(root_session.data)
    # pprint.pprint(root_session.print_nodes())
    # print(file_tree.data)
    # print(root_session.data)
    # iCloud_client = file_tree[0].name.get(file_tree[1].name)
    # dir = file_tree[-1]

# print(iCloud_client.dir(), iCloud_client[file_tree[1].name].dir())
# print(iCloud_client.dir())
# print(iCloud_client._root)

if dir not in iCloud_client.dir():
    sys.exit('Directory no present or misspelled!')


def upload_archive(local_path, iCloud_dir, existing_item=None, overwrite_intended=False):
    if overwrite_intended == True:
        try:
            renamed_name=f"{'.'.join(existing_item.name.split('.')[:-1])}_deleteme.{existing_item.name.split('.')[-1]}"
            renamed_response = existing_item.rename(renamed_name)['items'][0]
            # logger.info(renamed_response)

        except Exception as e:
            raise e

    os.chdir(local_path.parents[0])
    with open(local_path.name, 'rb') as archive:
        try:
            iCloud_client.drive[iCloud_dir].upload(archive)
        except Exception as e:
            raise e

    # pyicloud does not return a response from the upload method
    # easy path is to check from a separate session that it actually uploaded
    checker = pyicloud.PyiCloudService(user,password)
    if checker.drive[iCloud_dir].get(local_path.name).type == 'file':
        print(f"uploaded {local_path} successfully")
        # ok so it looks like name is much less consistent than the metadata returned from the rename call
        # so keep it, and use it here to delete
        # rather than child, access parent pyicloud.DriveService class and use its move_items_to_trash method
        if overwrite_intended == True:
            deleted_response = iCloud_client.drive.move_items_to_trash(
                renamed_response.get('drivewsid'),
                renamed_response.get('etag'),
                )
            print(deleted_response)

try:
    # items = iCloud_client.drive[dir].dir()
    items = iCloud_client.dir()
    print(items)
    
    if local.name in items:
        # existing_item = iCloud_client.drive[dir].get(local.name)
        existing_item = iCloud_client.get(local.name)
        # print(type(item))
        # <class 'pyicloud.services.drive.DriveNode'>
        if existing_item.type == 'file':
            overwrite_decision = click.prompt(
                f'Warning: file {local.name} already exists in /{dir}. \
                Would you like to overwrite it?\nEnter "Yes" or "No"'
                ).lower()

            #need to upgrade to python 3.10 to do a match case for this
            if overwrite_decision in ['yes', 'y', 'overwrite']:
                overwrite_intended = True

            if overwrite_intended != True:
                new_file_name = click.prompt(f'Enter a new name for the file [old name: {local.name}]')
                to_upload_path = local.parent.joinpath(new_file_name)
                shutil.copy(local, to_upload_path)
            
    upload_archive(
        local_path=to_upload_path,
        iCloud_dir=dir,
        existing_item=existing_item,
        overwrite_intended=overwrite_intended
        ) # do some logic about the existing file

except Exception as e:
    # upload_archive(local, dir)
    raise e