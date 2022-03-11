import click
import os
from pathlib import Path
import shutil

def select_file():
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

    return local

def traverse_file_tree(File_Tree_Node_object):
    pass

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