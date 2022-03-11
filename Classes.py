import pyicloud
import itertools

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
        # flatten a nested list with n layers of depth
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
        print(child.data)
        yield child
        for grandchild in descend_file_tree(child):
            print(grandchild.data)
            if grandchild.data.data['directChildrenCount'] == 0:
                yield
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