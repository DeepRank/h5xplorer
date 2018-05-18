from PyQt5 import QtWidgets
from h5xplorer.standarddialogs import *

def get_current_item(self,treeview,single=False):
    """Get the item(s) that was selected

    Args:
        treeview (HDF5TreeWidget): the treeview
        single (bool, optional): if true only single item possible

    Returns:
        TYPE: Description
    """
    items = [self._index_to_item(index) for index in treeview.selectedIndexes()]

    if single:
        if len(items)!=1:
            return
        items = items[0]
    return items

def get_current_hdf5_group(self,item):
    """Get the HDF5 group of the selected item

    Args:
        item (HDF5TreeItem): treeview item

    Returns:
        HDF5 group: the corresponding group
    """
    return self.root_item.data_file[item.name]

def get_group_data(group):
    """Get the dataset of the item

    Args:
        group (HDF5 group): group of the treeview item

    Returns:
        dataset or None: return np.array if the group has a dataset or None otherwise
    """
    try:
        return group.value
    except Exception as ex:
        return None

def get_actions(treeview,position,list_action):
    """Generate a singlelevel context menu of action and return the selected one

    Example:

    >>> list_operations = ['Print attrs','-','Plot Hist', 'Plot Map']
    >>> action,actions = get_actions(treeview,position,list_operations)
    >>> if action == actions['Print attrs']:
            send_dict_to_console(self,item,treeview)

    Args:
        treeview (HDF5TreeWidget): the treeview
        position (TYPE): Description
        list_action (list): List of string giving the action names

    Returns:
        actions: dict of QTMenu actions
        actions: the selected action
    """
    menu = QtWidgets.QMenu()
    actions = {}

    for operation in list_action:
        if operation == '-':
            menu.addSeparator()
        else:
            actions[operation] = menu.addAction(operation)
    selected_action = menu.exec_(treeview.viewport().mapToGlobal(position))
    return selected_action,actions

def get_multilevel_actions(treeview,position,list_action,sub_list):
    """Generate a multilevel context menu of action and return the selected one

    Example:

    >>> list_operations = ['Hit Rate','Av. Prec.']
    >>> list_subop = [['Train','Valid','Test'],['Train','Valid','Test']]
    >>> action,actions = get_multilevel_actions(treeview,position,list_operations,list_subop)

    Args:
        treeview (HDF5TreeWidget): the treeview
        position (TYPE): Description
        list_action (list): List of string giving the action names
        sub_list (list): list of string giving the subactions

    Returns:
        actions: dict of QTMenu actions
        actions: the selected action
    """
    menu = QtWidgets.QMenu()
    actions = {}

    for iop,operation in enumerate(list_action):
        if len(sub_list[iop]) == 0:
            actions[operation] = menu.addAction(operation)
        else:
            sub_menu = menu.addMenu(operation)
            for subop in sub_list[iop]:
                actions[(operation,subop)] = sub_menu.addAction(subop)

    selected_action = menu.exec_(treeview.viewport().mapToGlobal(position))
    return selected_action,actions

def send_dict_to_console(self,item,treeview):
    """Send a dictionany to the QT console

    Args:
        item (HDF5TreeItem): treeview item
        treeview (HDF5TreeWidget): the treeview
    """
    grp = get_current_hdf5_group(self,item)
    data = {'attrs':list(grp.attrs)}
    treeview.emitDict.emit(data)

def print_attributes(self,item,treeview):
    """Print the attribute in the console

    Args:
        item (HDF5TreeItem): treeview item
        treeview (HDF5TreeWidget): the treeview
    """
    grp = get_current_hdf5_group(self,item)
    attrs = list(grp.attrs)
    val = list(grp.attrs.values())
    print(attrs)
    print(val)
    data = {}
    for a in attrs:
        data[a] = 0
    treeview.emitDict.emit(data)

def get_user_values(varnames,vartypes='float',windowtitle='Enter Values'):
    """Get the values of variables from the users

    Args:
        varnames (list): list of strings of all the desired variables
        windowtitle (str, optional): Name of the window

    Returns:
        list: list of float of the desired variables
    """
    dialog = Dialog(varnames,vartypes=vartypes)
    dialog.exec_()
    return dialog.returnValues()