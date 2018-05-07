from PyQt5 import QtWidgets
from h5xplorer.standarddialogs import *
from h5xplorer.menu_tools import *


def plot_histogram(self,item,treeview,nbins=10):
    """Plot an histogram of the data

    Example:

    >>> def context_menu(self,treeview,position):
    >>>     all_item = get_current_item(self,treeview,single=False)
    >>>     item = all_item[0]
    >>>     list_operations = ['Plot Hist']
    >>>     action,actions = get_actions(treeview,position,list_operations)
    >>>     if action == actions['Plot Hist']:
                plot_histogram(self,item,treeview)

    Args:
        item (HDF5TreeItem): treeview item
        treeview (HDF5TreeWidget): treeview
        nbins (int, optional): number of bins in the histogram
    """

    grp = get_current_hdf5_group(self,item)
    value = get_group_data(grp)

    value = value.flatten()

    if value is not None:
        data_dict = {'_value':value}
        treeview.emitDict.emit(data_dict)

        cmd = "%matplotlib inline\n"
        cmd += "import matplotlib.pyplot as plt\nplt.hist(_value,%s)\nplt.show()\n" %nbins
        data_dict = {'exec_cmd':cmd}
        treeview.emitDict.emit(data_dict)

def plot_line(self,item,treeview):
    """Plot a line plot of a single item VS its index

    Example:

    >>> def context_menu(self,treeview,position):
    >>>     all_item = get_current_item(self,treeview,single=False)
    >>>     item = all_item[0]
    >>>     list_operations = ['Plot Line']
    >>>     action,actions = get_actions(treeview,position,list_operations)
    >>>     if action == actions['Plot Line']:
                plot_line(self,item,treeview)

    Args:
        item (HDF5TreeItem): treeview item
        treeview (HDF5TreeWidget): treeview
    """

    grp = get_current_hdf5_group(self,item)
    value = get_group_data(grp)

    if value is not None:
        data_dict = {'_value':value}
        treeview.emitDict.emit(data_dict)

        cmd = "%matplotlib inline\nimport matplotlib.pyplot as plt\nplt.plot(_value)\nplt.show()\n"
        data_dict = {'exec_cmd':cmd}
        treeview.emitDict.emit(data_dict)


def plot1D(self,item0,item1,treeview,plot='line'):
    """Plot a XY line or scatter plot of two items

    Note: You must be able to select multiple items to use this method.
    So you must create the app with:

    >>> app = h5xplorer(extended_selection=True)

    Example:

    >>> def context_menu(self,treeview,position):
    >>>     all_item = get_current_item(self,treeview,single=False)
    >>>     item0 = all_item[0]
    >>>     item1 = all_item[1]
    >>>     list_operations = ['Plot1D']
    >>>     action,actions = get_actions(treeview,position,list_operations)
    >>>     if action == actions['Plot1D']:
                plot1D(self,item0,item1,treeview)

    Args:
        item0 (HDF5TreeItem): treeview item for the X data
        item1 (HDF5TreeItem): treeview item for the Y data
        treeview (HDF5TreeWidget): treeview
        plot (str, optional): 'line' or 'scatter'
    """

    grp0 = get_current_hdf5_group(self,item0)
    grp1 = get_current_hdf5_group(self,item1)

    x = get_group_data(grp0)
    y = get_group_data(grp1)

    xlabel = item0.basename
    ylabel = item1.basename

    if x.ndim != 1 or y.ndim != 1 or x.shape!=y.shape:
        #show_error_message('Size Incompatible')
        return

    data_dict = {'_x':x,'_y':y}
    treeview.emitDict.emit(data_dict)

    data_dict = {}
    cmd  = "%matplotlib inline\nimport matplotlib.pyplot as plt\n"
    cmd += "fig,ax = plt.subplots()\n"

    if plot == 'scatter':
        cmd += "ax.scatter(_x,_y)\n"
    elif plot == 'line':
        cmd += "ax.plot(_x,_y)\n"

    cmd += "ax.set_xlabel('%s')\n" %xlabel
    cmd += "ax.set_ylabel('%s')\n" %ylabel
    cmd += "plt.show()\n"
    data_dict['exec_cmd'] = cmd
    treeview.emitDict.emit(data_dict)

def plot2d(self,item,treeview):
    """Plot a map of a 2D data array

    Example:

    >>> def context_menu(self,treeview,position):
    >>>     all_item = get_current_item(self,treeview,single=False)
    >>>     item = all_item[0]
    >>>     list_operations = ['Plot2D']
    >>>     action,actions = get_actions(treeview,position,list_operations)
    >>>     if action == actions['Plot2D']:
                plot2D(self,item,treeview)

    Args:
        item (HDF5TreeItem): treeview item
        treeview (HDF5TreeWidget): treeview
    """


    grp = get_current_hdf5_group(self,item)
    data = get_group_data(grp)

    if data.ndim != 2:
        return

    data_dict = {'_map':data}
    treeview.emitDict.emit(data_dict)

    data_dict = {}
    cmd  = "%matplotlib inline\nimport matplotlib.pyplot as plt\n"
    cmd += "plt.imshow(_map)\n"
    cmd += "plt.show()\n"
    data_dict['exec_cmd'] = cmd
    treeview.emitDict.emit(data_dict)