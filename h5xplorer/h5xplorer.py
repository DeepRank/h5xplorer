#!/usr/bin/env python


#################################################################################
##
##
#################################################################################

import os,sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QAbstractItemModel, QFile, QIODevice, QModelIndex, Qt, QItemSelectionModel
from PyQt5.QtCore import pyqtSignal,pyqtSlot
from PyQt5.QtWidgets import QApplication, QTreeView, QFrame, QFileIconProvider, QMenuBar
import h5py
import functools

# Import the console machinery from ipython
from qtconsole.rich_ipython_widget import RichIPythonWidget,RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport
import types



class QIPythonWidget(RichJupyterWidget):

    """
    Convenience class for a live IPython console widget.
    We can replace the standard banner using the customBanner argument
    https://stackoverflow.com/questions/11513132/embedding-ipython-qt-console-in-a-pyqt-application

    possible colors lightbg,linux,nocolor
    """


    def __init__(self,customBanner=None,colors='lightbg',*args,**kwargs):
        if not customBanner is None: self.banner=customBanner
        super(QIPythonWidget, self).__init__(*args,**kwargs)
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel_manager.kernel.gui = 'qt4'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()
        self.set_default_style(colors=colors)
        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            guisupport.get_app_qt4().exit()
        self.exit_requested.connect(stop)

    def pushVariables(self,variableDict):
        """ Given a dictionary containing name / value pairs, push those variables to the IPython console widget """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clearTerminal(self):
        """ Clears the terminal """
        self._control.clear()

    def printText(self,text):
        """ Prints some plain text to the console """
        self._append_plain_text(text)

    def executeCommand(self,command,hidden=False,interactive=False):
        """ Execute a command in the frame of the console widget """
        self.execute(source=command,hidden=hidden,interactive=interactive)

    def import_value(self,HDF5Object):
        HDF5Object.emitDict.connect(self.get_value)

    @pyqtSlot(dict)
    def get_value(self,variableDict):

        # exectute a command
        keys = list(variableDict.keys())
        if keys[0].startswith('exec_cmd'):
            for k,cmd in variableDict.items():
                self._execute(cmd,False)

        # push a variable in the console
        # print it if the name doesnt start with _
        else:
            self.pushVariables(variableDict)
            for k in variableDict:
                if not k.startswith('_'):
                    self.executeCommand('%s' %k)

class DummyHDF5Group(dict):
    def __init__(self,dictionary, attrs ={}, name="DummyHDF5Group"):
        super(DummyHDF5Group, self).__init__()
        self.attrs = attrs
        for key in dictionary:
            self[key] = dictionary[key]
        self.name = name
        self.basename = name

    file = None
    parent = None

class HDF5TreeItem(object):

    '''
    Item in an HDF5 Tree
    https://github.com/nanophotonics/nplab/blob/master/nplab/ui/hdf5_browser.py
    '''

    def __init__(self,data_file,parent,name,row):

        """Create a new item for an HDF5 tree
        data_file : HDF5 data file
            This is the file (NB must be the top-level group) containing everything
        parent : HDF5TreeItem
            The parent of the current item
        name : string
            The name of the current item (should be parent.name plus an extra component)
        row : int
            The index of the current item in the parent's children.
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
            self._has_children = hasattr(self.data_file[self.name],"keys")
        return self._has_children

    _children = None
    @property
    def children(self):
        if self.has_children is False:
            return []
        if self._children is None:
            keys = list(self.data_file[self.name].keys())
            self._children = [HDF5TreeItem(self.data_file, self, self.name.rstrip("/") + "/" + k, i) for i, k in enumerate(keys)]
        return self._children

    def purge_children(self):
        """Empty the cached list of children"""
        try:
            if self._children is not None:
                for child in self._children:
                    child.purge_children() # We must delete them all the way down!
                    self._children.remove(child)
                    del child # Not sure if this is needed...
                self._children = None
            self._has_children = None
        except:
            print("{} failed to purge its children".format(self.name))

    @property
    def h5item(self):
        """The underlying HDF5 item for this tree item."""
        assert self.name in self.data_file, "Error, {} is no longer a valid HDF5 item".format(self.name)
        return self.data_file[self.name]

    def __del__(self):
        self.purge_children()

class HDF5ItemModel(QtCore.QAbstractItemModel):
    """
    This model takes its data from an HDF5 Group for display in a tree.
    It loads the file as the tree is expanded for speed - in the future it might implement sanity checks to
    abort loading very long folders.
    https://github.com/nanophotonics/nplab/blob/master/nplab/ui/hdf5_browser.py
    """

    def __init__(self,data_group,res):

        super().__init__()
        self.root_item = None
        self.data_group = data_group
        self.iconProvider = QFileIconProvider()
        self.res = res

        #self.selections = QItemSelectionModel(self)

    _data_group = None
    @property
    def data_group(self,new_data_group):
        if self.root_item is not None:
            del self.root_item
        self._data_group = new_data_group
        self.root_item = HDF5TreeItem(new_data_group.file,None,new_data_group.name,0)

    @data_group.setter
    def data_group(self, new_data_group):
        """Set the data group represented by the model"""
        if self.root_item is not None:
            del self.root_item
        self._data_group = new_data_group
        self.root_item = HDF5TreeItem(new_data_group.file, None, new_data_group.name, 0)

    def _index_to_item(self,index):
        ''' return tthe HDF5Item for a given index'''
        if index.isValid():
            return index.internalPointer()
        else:
            return self.root_item


    def index(self,row,column,parent_index):
        """Return the index of the <row>th child of parent
        :type row: int
        :type column: int
        :type parent_index: QtCore.QModelIndex
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

            # for the targets we pint the name and values
            if item.parent.basename == 'targets':
                value = item.data_file[item.name].value
                return "{:10s}".format(item.basename) + ' %1.3f' %value

            # for the rest just the values
            return self._index_to_item(index).basename

        # elif role == QtCore.Qt.WhatsThisRole:
        #     if not self._index_to_item(index)._has_children:
        #         print(self._index_to_item(index).basename)
        #     return print(self._index_to_item(index).basename)

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
        items = [self._index_to_item(index) for index in treeview.selectedIndexes()]
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
        treeview.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.SelectedClicked)
        treeview.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)

        # Set up a callback to allow us to customise the context menu
        treeview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        treeview.customContextMenuRequested.connect(functools.partial(self.context_menu, treeview))

    '''
    def context_menu(self, treeview, position):

        """Generate a right-click menu for the items"""

        # make sure tha there is only one item selected
        items = [self._index_to_item(index) for index in treeview.selectedIndexes()]
        if len(items)!=1:
            return
        item = items[0]

        try:
            _type = self.root_item.data_file[item.name].attrs['type']

            if _type == 'molecule':
                self._context_mol(item,treeview,position)

            if _type == 'sparse_matrix':
                self._context_sparse(item,treeview,position)

            if _type == 'epoch':
                self._context_epoch(item,treeview,position)

            if _type == 'losses':
                self._context_losses(item,treeview,position)

        except:
            return

    def _context_mol(self,item,treeview,position):

        menu = QtWidgets.QMenu()
        actions = {}
        list_operations = ['Load in PyMol','Load in VMD','PDB2SQL']

        for operation in list_operations:
            actions[operation] = menu.addAction(operation)
        action = menu.exec_(treeview.viewport().mapToGlobal(position))

        if action == actions['Load in VMD']:
            _,cplx_name,mol_name = item.name.split('/')
            molgrp = self.root_item.data_file[item.name]
            viztools.create3Ddata(mol_name,molgrp)
            viztools.launchVMD(mol_name,self.res)

        if action == actions['Load in PyMol']:
            _,cplx_name,mol_name = item.name.split('/')
            molgrp = self.root_item.data_file[item.name]
            viztools.create3Ddata(mol_name,molgrp)
            viztools.launchPyMol(mol_name)

        if action == actions['PDB2SQL']:
            _,cplx_name,mol_name = item.name.split('/')
            molgrp = self.root_item.data_file[item.name]
            db = pdb2sql(molgrp['complex'].value)
            treeview.emitDict.emit({'sql_' + item.basename: db})

    def _context_sparse(self,item,treeview,position):

        menu = QtWidgets.QMenu()
        actions = {}
        list_operations = ['Load Matrix','Plot Histogram']

        for operation in list_operations:
            actions[operation] = menu.addAction(operation)
        action = menu.exec_(treeview.viewport().mapToGlobal(position))
        name = item.basename + '_' + item.name.split('/')[2]

        if action == actions['Load Matrix']:

            subgrp = item.data_file[item.name]
            data_dict = {}
            if not subgrp.attrs['sparse']:
                data_dict[item.name] =  subgrp['value'].value
            else:
                molgrp = item.data_file[item.parent.parent.parent.name]
                grid = {}
                lx = len(molgrp['grid_points/x'].value)
                ly = len(molgrp['grid_points/y'].value)
                lz = len(molgrp['grid_points/z'].value)
                shape = (lx,ly,lz)
                spg = sparse.FLANgrid(sparse=True,index=subgrp['index'].value,value=subgrp['value'].value,shape=shape)
                data_dict[name] =  spg.to_dense()
            treeview.emitDict.emit(data_dict)

        if action == actions['Plot Histogram']:

            value = item.data_file[item.name]['value'].value
            data_dict = {'value':value}
            treeview.emitDict.emit(data_dict)

            cmd = "%matplotlib inline\nimport matplotlib.pyplot as plt\nplt.hist(value,25)\nplt.show()\n"            
            data_dict = {'exec_cmd':cmd}
            treeview.emitDict.emit(data_dict)

    def _context_epoch(self,item,treeview,position):

        menu = QtWidgets.QMenu()
        actions = {}
        list_operations = ['Scatter Plot']

        for operation in list_operations:
            actions[operation] = menu.addAction(operation)
        action = menu.exec_(treeview.viewport().mapToGlobal(position))

        if action == actions['Scatter Plot']:


            values = []
            train_out = item.data_file[item.name+'/train/outputs'].value
            train_tar = item.data_file[item.name+'/train/targets'].value
            values.append([x for x in train_out])
            values.append([x for x in train_tar])


            valid_out = item.data_file[item.name+'/valid/outputs'].value
            valid_tar = item.data_file[item.name+'/valid/targets'].value
            values.append([x for x in valid_tar])
            values.append([x for x in valid_out])


            test_out = item.data_file[item.name+'/test/outputs'].value
            test_tar = item.data_file[item.name+'/test/targets'].value
            values.append([x for x in test_tar])
            values.append([x for x in test_out])

            vmin = np.array([x for a in values for x in a]).min()
            vmax = np.array([x for a in values for x in a]).max()
            delta = vmax-vmin
            values.append([vmax + 0.1*delta])
            values.append([vmin - 0.1*delta])

            data_dict = {'_values':values}
            treeview.emitDict.emit(data_dict)

            data_dict = {}
            cmd  = "%matplotlib inline\nimport matplotlib.pyplot as plt\n"
            cmd += "fig,ax = plt.subplots()\n"
            cmd += "ax.scatter(_values[0],_values[1],c='red',label='train')\n"
            cmd += "ax.scatter(_values[2],_values[3],c='blue',label='valid')\n"
            cmd += "ax.scatter(_values[4],_values[5],c='green',label='test')\n"
            cmd += "legen = ax.legend(loc='upper left')\n"
            cmd += "ax.set_xlabel('Targets')\n"
            cmd += "ax.set_ylabel('Predictions')\n"
            cmd += "ax.plot([_values[-2],_values[-1]],[_values[-2],_values[-1]])\n"
            cmd += "plt.show()\n" 
            data_dict['exec_cmd'] = cmd
            treeview.emitDict.emit(data_dict)

    def _context_losses(self,item,treeview,position):

        menu = QtWidgets.QMenu()
        actions = {}
        list_operations = ['Plot Losses']

        for operation in list_operations:
            actions[operation] = menu.addAction(operation)
        action = menu.exec_(treeview.viewport().mapToGlobal(position))

        if action == actions['Plot Losses']:


            values = []
            test = item.data_file[item.name+'/test'].value
            train = item.data_file[item.name+'/train'].value
            valid = item.data_file[item.name+'/valid'].value
            values.append([x for x in train])
            values.append([x for x in valid])
            values.append([x for x in test])

            data_dict = {'_values':values}
            treeview.emitDict.emit(data_dict)

            data_dict = {}
            cmd  = "%matplotlib inline\nimport matplotlib.pyplot as plt\n"
            cmd += "fig,ax = plt.subplots()\n"
            cmd += "plt.plot(_values[0],c='red',label='train')\n"
            cmd += "plt.plot(_values[1],c='blue',label='valid')\n"
            cmd += "plt.plot(_values[2],c='green',label='test')\n"
            cmd += "legen = ax.legend(loc='upper right')\n"
            cmd += "ax.set_xlabel('Epoch')\n"
            cmd += "ax.set_ylabel('Losses')\n"
            cmd += "plt.show()\n"
            data_dict['exec_cmd'] = cmd
            treeview.emitDict.emit(data_dict)
    '''

class HDF5TreeWidget(QtWidgets.QTreeView):


    emitDict = pyqtSignal(dict)

    """A TreeView for looking at an HDF5 tree"""
    def __init__(self, datafile,res=None, menu=None, **kwargs):
        """Create a TreeView widget that views the contents of an HDF5 tree.
        Arguments:
            datafile : nplab.datafile.Group
            the HDF5 tree to show
        Additional keyword arguments are passed to the QTreeView constructor.
        You may want to include parent, for example."""
        QtWidgets.QTreeView.__init__(self, **kwargs)

        self.model = HDF5ItemModel(datafile,res)
        self.model.context_menu = types.MethodType(menu, self.model)
        self.model.set_up_treeview(self)
        self.sizePolicy().setHorizontalStretch(0)
        self.mouseDoubleClickEvent = self.doubleClicked

    def selected_h5item(self):
        """Return the current selection as an HDF5 item."""
        return self.model.selected_h5item_from_view(self)

    def doubleClicked(self,event):

        '''
        Handle the double click on the different items
        If the item has no children its name/value are emitted
        and are pushed in the iPython console
        '''

        # get the current item
        items = [self.model._index_to_item(index) for index in self.selectedIndexes()]
        if len(items)!=1:
            return
        item=items[0]

        # if the item has no children we push the raw data
        if not item._has_children:
            name = item.basename + '_' + item.name.split('/')[2]
            self.emitDict.emit({name: item.data_file[item.name].value})

        # or we skip
        else:
            return

class HDF5Browser(QtWidgets.QWidget):
    """A Qt Widget for browsing an HDF5 file and graphing the data.
    """

    def __init__(self, data_file, res, func_menu, parent=None):

        super(HDF5Browser, self).__init__(parent)

        self.setWindowTitle("h5Xplorer")
        self.data_file = data_file
        self.res = res
        ip = QtWidgets.QFileIconProvider()
        fileinfo = QtCore.QFileInfo(data_file.name)
        icon = ip.icon(QFileIconProvider.Drive)

        # the tree widget
        self.treeWidget = HDF5TreeWidget(data_file,res=self.res,menu=func_menu,parent=self)
        self.selection_model = self.treeWidget.selectionModel()

        # push button to load data
        self.load_tree_button = QtWidgets.QPushButton() #Create a refresh button
        self.load_tree_button.setIcon(icon)
        self.load_tree_button.setIconSize(QtCore.QSize(24,24))
        self.load_tree_button.clicked.connect(self.load_new_data)

        #  widget that contains the toolbar and the treeview
        self.treelayoutwidget = QtWidgets.QWidget()
        self.treelayoutwidget.setLayout(QtWidgets.QVBoxLayout())
        self.treelayoutwidget.layout().addWidget(self.treeWidget)
        self.treelayoutwidget.layout().addWidget(self.load_tree_button)

        #the Ipython console
        self.ipyConsole = QIPythonWidget(customBanner="Welcome to the DeepRank Explorer\n")

        # make the splitt window
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.treelayoutwidget)       #Add newly constructed widget (treeview and button) to the splitter
        splitter.addWidget(self.ipyConsole)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(splitter)

        # make the connection between the tree and the iPython console
        self.ipyConsole.import_value(self.treeWidget)


    def load_new_data(self):

        fname = QtWidgets.QFileDialog.getOpenFileName(self,'Open File','./')
        fname = fname[0]
        if os.path.isfile(fname):
            print('Load File ' + fname)
            mol_name = os.path.splitext(os.path.basename(fname))[0]
            if mol_name not in self.data_file:
                self.data_file[mol_name] = h5py.ExternalLink(fname,'/')
                self.treeWidget.model.refresh_tree()

    def sizeHint(self):
        #return QtCore.QSize(int(self.res.width()/2),int(self.res.height()))
        return QtCore.QSize(1000,600)

    def attach_menu(self,menu_func):
        self.treeview.model.context_menu = types.MethodType(menu_func,self.treeview.model)

class h5xplorer(object):

    def __init__(self,func_menu):

        app = QApplication(sys.argv)
        res = app.desktop().screenGeometry()
        w,h = res.width(),res.height()

        data_file = h5py.File('_tmp.hdf5','w')

        ui = HDF5Browser(data_file,res,func_menu)

        ui.show()
        sys.exit(app.exec_())
        data_file.close()

if __name__ == '__main__':

    app = h5xplorer(menu.context_menu)