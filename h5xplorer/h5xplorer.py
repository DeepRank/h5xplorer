#!/usr/bin/env python

############################################################################################
# Source : https://github.com/nanophotonics/nplab/blob/master/nplab/ui/hdf5_browser.py
# https://stackoverflow.com/questions/11513132/embedding-ipython-qt-console-in-a-pyqt-application
##########################################################################################

import os
import sys
import warnings
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QAbstractItemModel, QFile, QIODevice, QModelIndex, Qt, QItemSelectionModel
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QTreeView, QFrame, QFileIconProvider, QMenuBar, QErrorMessage, QMessageBox
import h5py
import functools
import numpy as np

# Import the console machinery from ipython
from qtconsole.rich_ipython_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport
import types

from h5xplorer.default_menu import default_context_menu


class QIPythonWidget(RichJupyterWidget):

    def __init__(self, customBanner=None, colors='lightbg', baseimport=None, *args, **kwargs):
        """Convenience class for a live IPython console widget.
        Adapted from the pyQT example

        Attributes:
            banner (str): banner on top of the console
            kernel_client (kernel_manager.client): client for the kernel
            kernel_manager (QtInProcessKernelManager): kernel manager

        Args:
            customBanner (str, optional): Custom banner
            colors (str, optional): Colorschem for the console: lightbg,linux,nocolor
            *args: Description
            **kwargs: Description
        """
        super(QIPythonWidget, self).__init__(*args, **kwargs)

        if not customBanner is None:
            self.banner = customBanner

        # create an Inprocess kernel
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel_manager.kernel.gui = 'qt4'

        self.kernel_client = self._kernel_manager.client()
        self.kernel_client.start_channels()

        # set the colorscheme
        self.set_default_style(colors=colors)

        # exectute the base import
        if baseimport is not None:
            if os.path.isfile(baseimport):
                with open(baseimport, 'r') as f:
                    cmd = f.readlines()
                cmd = ''.join(cmd)
                try:
                    self._execute(cmd, False)
                except:
                    self.printText('Import of %s failed' % baseimport)

        self.exit_requested.connect(self.stop)

    def pushVariables(self, variableDict):
        """ Given a dictionary containing name / value pairs,
        push those variables to the IPython console widget

        Args:
            variableDict: dict of var {names: value}

        """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clearTerminal(self):
        """ Clears the terminal """
        self._control.clear()

    def printText(self, text):
        """ Prints some plain text to the console.

        Args:
            text (str): text to be printed

        """
        self._append_plain_text(text)

    def executeCommand(self, command, hidden=False, interactive=False):
        """Execute a command in the frame of the console widget

        Args:
            command (str): Command to execute
            hidden (bool, optional): hid the command or not
            interactive (bool, optional): Interactive Mode
        """
        self.execute(source=command, hidden=hidden,
                     interactive=interactive)

    def import_value(self, HDF5Object):
        """Import the value of a HDF5 object

        Args:
            HDF5Object (HDF5 item): Instance of a HDF5 item
        """
        HDF5Object.emitDict.connect(self.get_value)

    @pyqtSlot(dict)
    def get_value(self, variableDict):
        """Get the dict of variables emmitted by the treeview.
        Note: if the name of variable starts with _ the value is NOT
        printed in the console.

        Args:
            variableDict (dict): dict of variables {name: value}
        """
        # exectute a command
        keys = list(variableDict.keys())
        if keys[0].startswith('exec_cmd'):
            for k, cmd in variableDict.items():
                self._execute(cmd, False)

        # push a variable in the console
        # print it if the name doesnt start with _
        else:
            self.pushVariables(variableDict)
            for k in variableDict:
                if not k.startswith('_'):
                    self.executeCommand('%s' % k)

    def stop():
        """Stop the kernel."""
        self.kernel_client.stop_channels()
        self.kernel_manager.shutdown_kernel()
        guisupport.get_app_qt4().exit()


class DummyHDF5Group(dict):

    def __init__(self, dictionary, attrs={}, name="DummyHDF5Group"):
        """Dummy HDF5 group created sometimes ....

        Args:
            dictionary (dict):
            attrs (dict, optional):
            name (str, optional): Name of the group
        """
        super(DummyHDF5Group, self).__init__()
        self.attrs = attrs
        for key in dictionary:
            self[key] = dictionary[key]
        self.name = name
        self.basename = name

    file = None
    parent = None


class HDF5TreeItem(object):

    def __init__(self, data_file, parent, name, row):
        """Create a new item for an HDF5 tree

        Args:
            data_file ( HDF5 data file): This is the file (NB must be the top-level group) containing everything
            parent (HDF5TreeItem): The parent of the current item
            name (string): The name of the current item (should be parent.name plus an extra component)
            row (int): The index of the current item in the parent's children.
        """

        self.data_file = data_file
        self.parent = parent
        self.name = name
        self.row = row

        if parent is not None:
            assert name.startswith(parent.name)
            assert name in data_file

    @property
    def basename(self):
        return os.path.basename(self.name)

    _has_children = None
    @property
    def has_children(self):
        if self._has_children is None:
            self._has_children = hasattr(
                self.data_file[self.name], "keys")
        return self._has_children

    _children = None
    @property
    def children(self):
        if self.has_children is False:
            return []
        if self._children is None:
            keys = list(self.data_file[self.name].keys())
            self._children = [HDF5TreeItem(self.data_file, self, self.name.rstrip(
                "/") + "/" + k, i) for i, k in enumerate(keys)]
        return self._children

    def purge_children(self):
        """Empty the cached list of children."""

        try:
            if self._children is not None:
                for child in self._children:
                    child.purge_children()  # We must delete them all the way down!
                    self._children.remove(child)
                    del child  # Not sure if this is needed...
                self._children = None
            self._has_children = None
        except:
            print("{} failed to purge its children".format(self.name))

    @property
    def h5item(self):
        """The underlying HDF5 item for this tree item."""

        assert self.name in self.data_file, "Error, {} is no longer a valid HDF5 item".format(
            self.name)
        return self.data_file[self.name]

    def __del__(self):
        self.purge_children()


class HDF5ItemModel(QtCore.QAbstractItemModel):

    """This model takes its data from an HDF5 Group for display in a tree.
    It loads the file as the tree is expanded for speed - in the future it might implement sanity checks to
    abort loading very long folders.
    """

    def __init__(self, data_group, res, extended_selection):
        """Init the class

        Args:
            data_group (HDF5 grup): HDF5 group
            res (qt resolution): size of the app
            extended_selection (bool): allow multiple selection
        """
        super().__init__()
        self.root_item = None
        self.data_group = data_group
        self.iconProvider = QFileIconProvider()
        self.res = res
        self.extended_selection = extended_selection

    _data_group = None
    @property
    def data_group(self, new_data_group):
        if self.root_item is not None:
            del self.root_item
        self._data_group = new_data_group
        self.root_item = HDF5TreeItem(
            new_data_group.file, None, new_data_group.name, 0)

    @data_group.setter
    def data_group(self, new_data_group):
        """Set the data group represented by the model."""

        if self.root_item is not None:
            del self.root_item
        self._data_group = new_data_group
        self.root_item = HDF5TreeItem(
            new_data_group.file, None, new_data_group.name, 0)

    def _index_to_item(self, index):
        '''return the HDF5Item for a given index.

        Args:
            index (int): index of the item

        Returns:
            HDF5item: corresponding item
        '''

        if index.isValid():
            return index.internalPointer()
        else:
            return self.root_item

    def index(self, row, column, parent_index):
        """Return the index of the <row>th child of parent.

        Args:
            row (int): row index
            column (int): column index
            parent_index (QtCore.QModelIndex): Parent

        """
        try:
            parent = self._index_to_item(parent_index)
            return self.createIndex(row, column, parent.children[row])
        except:
            return QtCore.QModelIndex()

    def parent(self, index=None):
        """Find the index of the parent of the item at a given index."""
        try:
            parent = self._index_to_item(index).parent
            return self.createIndex(parent.row, 0, parent)
        except:
            # Something went wrong with finding the parent so return an invalid index
            return QtCore.QModelIndex()

    def flags(self, index):
        """Return flags telling Qt what to do with the item"""
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def data(self, index, role):
        """The data represented by this item."""
        if not index.isValid():
            return None

        if role == QtCore.Qt.DisplayRole:
            item = self._index_to_item(index)

            # If the dataset is one number we print the value in the name
            # if item.parent.basename == 'targets':
            try:
                value = item.data_file[item.name].value
                if not isinstance(value, np.ndarray):
                    return "{:10s}".format(item.basename) + '\tvalue : %1.3e' % value

                else:
                    if value.shape == (1,):
                        return "{:10s}".format(item.basename) + '\tvalue : %1.3e' % value
                    else:
                        dims = ' x '.join(
                            map(lambda x: str(x), value.shape))
                        return "{:10s}".format(item.basename) + '\tsize : ' + dims
            except Exception as ex:
                pass
            # for the rest just the values
            return self._index_to_item(index).basename

        elif role == Qt.DecorationRole:
            if self._index_to_item(index)._has_children:
                return self.iconProvider.icon(QFileIconProvider.Folder)
            else:
                return self.iconProvider.icon(QFileIconProvider.File)

        else:
            return None

    def headerData(self, section, orientation, role=None):
        """Return the header names - an empty string here!"""
        return [""]

    def rowCount(self, index):
        """The number of rows exposed by the model"""
        try:
            item = self._index_to_item(index)
            assert item.has_children
            return len(item.children)
        except:
            # if it doesn't have keys, assume there are no children.
            return 0

    def hasChildren(self, index):
        """Whether or not this object has children"""
        return self._index_to_item(index).has_children

    def columnCount(self, index=None, *args, **kwargs):
        """Return the number of columns"""
        return 1

    def refresh_tree(self):
        """Reload the HDF5 tree, resetting the model
        This causes all cached HDF5 tree information to be deleted, and any views
        using this model will automatically reload.
        """
        self.beginResetModel()
        self.root_item.purge_children()
        self.endResetModel()

    def selected_h5item_from_view(self, treeview):
        """Given a treeview object, return the selection, as an HDF5 object, or a work-alike for multiple selection.
        If one item is selected, we will return the HDF5 group or dataset that is selected.  If multiple items are
        selected, we will return a dummy HDF5 group containing all selected items.
        """
        items = [self._index_to_item(index)
                 for index in treeview.selectedIndexes()]
        if len(items) == 1:
            return items[0].h5item
        elif len(items) > 1:
            return DummyHDF5Group({item.name: item.h5item for item in items})
        else:
            return None

    def set_up_treeview(self, treeview):
        """Correctly configure a QTreeView to use this model.
        This will set the HDF5ItemModel as the tree's model (data source), and in the future
        may set up context menus, etc. as appropriate."""

        # Make the tree view use this object as its model
        treeview.setModel(self)
        treeview.setAlternatingRowColors(True)
        treeview.setEditTriggers(
            QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.SelectedClicked)
        treeview.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectItems)

        # Set up a callback to allow us to customise the context menu
        treeview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        treeview.customContextMenuRequested.connect(
            functools.partial(self.context_menu, treeview))

        # set the selection Mode
        if self.extended_selection:
            treeview.setSelectionMode(
                QtWidgets.QAbstractItemView.ExtendedSelection)


class HDF5TreeWidget(QtWidgets.QTreeView):

    emitDict = pyqtSignal(dict)

    """A TreeView for looking at an HDF5 tree"""

    def __init__(self, datafile, res=None, menu=None, extended_selection=False, **kwargs):
        """Create a TreeView widget that views the contents of an HDF5 tree.
        Arguments:
            datafile : nplab.datafile.Group
            the HDF5 tree to show
        Additional keyword arguments are passed to the QTreeView constructor.
        You may want to include parent, for example."""
        QtWidgets.QTreeView.__init__(self, **kwargs)

        self.model = HDF5ItemModel(
            datafile, res, extended_selection=extended_selection)
        self.model.context_menu = types.MethodType(menu, self.model)
        self.model.set_up_treeview(self)
        self.sizePolicy().setHorizontalStretch(0)
        self.mouseDoubleClickEvent = self.doubleClicked

    def selected_h5item(self):
        """Return the current selection as an HDF5 item."""
        return self.model.selected_h5item_from_view(self)

    def doubleClicked(self, event):
        '''
        Handle the double click on the different items
        If the item has no children its name/value are emitted
        and are pushed in the iPython console
        '''

        # get the current item
        items = [self.model._index_to_item(
            index) for index in self.selectedIndexes()]
        if len(items) != 1:
            return
        item = items[0]

        # if the item has no children we push the raw data
        if not item._has_children:
            try:
                name = item.basename + '_' + item.name.split('/')[2]
                self.emitDict.emit(
                    {name: item.data_file[item.name].value})
            except:
                self.emitDict.emit({name: 'Corrupted data'})

        # or we skip
        else:
            return


class HDF5Browser(QtWidgets.QWidget):
    """A Qt Widget for browsing an HDF5 file and graphing the data.
    """

    def __init__(self, data_file, res, func_menu, baseimport=None, extended_selection=False, parent=None):

        super(HDF5Browser, self).__init__(parent)

        self.setWindowTitle("h5Xplorer")
        self.data_file = data_file
        self.res = res
        ip = QtWidgets.QFileIconProvider()
        fileinfo = QtCore.QFileInfo(data_file.name)
        icon = ip.icon(QFileIconProvider.Drive)

        # the tree widget
        if func_menu is None:
            def func_menu(a, b, c): return None
        self.treeWidget = HDF5TreeWidget(data_file, res=self.res, menu=func_menu,
                                         extended_selection=extended_selection, parent=self)
        self.selection_model = self.treeWidget.selectionModel()

        # push button to load data
        self.load_tree_button = QtWidgets.QPushButton()  # Create a refresh button
        self.load_tree_button.setIcon(icon)
        self.load_tree_button.setIconSize(QtCore.QSize(24, 24))
        self.load_tree_button.clicked.connect(self.load_new_data)

        #  widget that contains the toolbar and the treeview
        self.treelayoutwidget = QtWidgets.QWidget()
        self.treelayoutwidget.setLayout(QtWidgets.QVBoxLayout())
        self.treelayoutwidget.layout().addWidget(self.treeWidget)
        self.treelayoutwidget.layout().addWidget(self.load_tree_button)

        # the Ipython console
        self.ipyConsole = QIPythonWidget(baseimport=baseimport)

        # make the splitt window
        splitter = QtWidgets.QSplitter()
        # Add newly constructed widget (treeview and button) to the splitter
        splitter.addWidget(self.treelayoutwidget)
        splitter.addWidget(self.ipyConsole)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(splitter)

        # make the connection between the tree and the iPython console
        self.ipyConsole.import_value(self.treeWidget)

    def load_new_data(self):

        fname = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open File', './')
        fname = fname[0]
        if os.path.isfile(fname):
            if h5py.is_hdf5(fname):
                mol_name = os.path.splitext(
                    os.path.basename(fname))[0]
                if mol_name not in self.data_file:
                    self.data_file[mol_name] = h5py.ExternalLink(
                        fname, '/')
                    self.treeWidget.model.refresh_tree()
            else:
                errorMessageDialog = QMessageBox.information(self,
                                                             "File Invalid", "Not a HDF5 File. if you're trying a netCDF3 file convert it to netCDf4 before")

    def sizeHint(self):
        # return QtCore.QSize(int(self.res.width()/2),int(self.res.height()))
        return QtCore.QSize(1000, 600)

    def attach_menu(self, menu_func):
        self.treeview.model.context_menu = types.MethodType(
            menu_func, self.treeview.model)


class h5xplorer(object):

    def __init__(self, func_menu=default_context_menu, baseimport=None, extended_selection=False):

        app = QApplication(sys.argv)
        res = app.desktop().screenGeometry()
        w, h = res.width(), res.height()

        self.tmp_file = '.tmp.hdf5'
        self.data_file = h5py.File(self.tmp_file, 'w')

        if baseimport is not None:
            if not os.path.isfile(baseimport):
                warnings.warn('Baseimport %s not found' %
                              baseimport, Warning)

        ui = HDF5Browser(self.data_file, res,
                         func_menu,
                         baseimport=baseimport,
                         extended_selection=extended_selection)

        ui.show()
        app.aboutToQuit.connect(self.cleanup)
        sys.exit(app.exec_())

    def cleanup(self):
        self.data_file.close()
        os.remove(self.tmp_file)
