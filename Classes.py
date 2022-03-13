import pyicloud
import itertools

class File_Tree_Node():
    def __init__(self, drive_node, parent=None):
        # if isinstance(drive_node, File_Tree_Node):
        #     print('tried to instantiate existing node!')
        #     return None
        self.drive_node = drive_node
        self.children = self._get_children()
        self.type = self._get_type()
        self.parent = parent

    def _get_children(self):
        # DriveNode.get_children() method returns list _children
        # while we have an iterable, we need to pass up 3 attributes for use in the File_Tree_Node class level
        #   1. identify type of children
        #   2. assign parent to children (so that File_Tree_Node __init__ method can be called on them)
        #   3. set the child name as a key, so that the dict may be accessed by name
        #
        # This is a classic tree so child.parent = self
        
        def _reducer(child):

            return {'child': child, 'parent': self, 'type': child.type, child.name: child}

        return [_reducer(x) for x in self.drive_node.get_children()]

    def _get_type(self):
        return self.drive_node.type

    def _get_child_folders(self):
        return (File_Tree_Node(x['child'], x['parent']) for x in self.children if x['child'].type == 'folder')
    
    def _get_child_files(self):
        return (File_Tree_Node(x['child'], x['parent']) for x in self.children if x['child'].type == 'file')

    def _get_child_nodes(self):
        # flatten a nested list with n layers of depth
        return itertools.chain(self.get_child_folders(), self.get_child_files())

    def formatter(self):
        def _root(x):
            if x.drive_node.data.get('docwsid') == 'root': return 'root'
            else: return x.drive_node.name

        def _files(x):
            return [i.drive_node.name for i in x._get_child_files()]

        def _folders(x):
            return [{'folder': i.drive_node.name, 'contents': i.drive_node.data['directChildrenCount']} for i in x._get_child_folders()]

        return({
            "Current Directory": _root(self),
            "Files": _files(self),
            "Folders": _folders(self)
            })

def build_file_tree(starting_node):
    if isinstance(starting_node, pyicloud.services.drive.DriveNode):
        root = File_Tree_Node(starting_node)
    else:
        root = File_Tree_Node(starting_node.drive_node, parent=starting_node.parent)

    return root, root.formatter()

def descend_file_tree(starting_node):
    if not isinstance(starting_node, File_Tree_Node):
        return

    for child in starting_node._get_child_folders():
        print(child.drive_node)
        yield child
        for grandchild in descend_file_tree(child):
            print(grandchild.drive_node)
            if grandchild.drive_node.data['directChildrenCount'] == 0:
                yield
            yield grandchild
