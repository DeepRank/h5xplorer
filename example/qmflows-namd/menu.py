import viztools
from PyQt5 import QtWidgets
from deeprank.tools import pdb2sql, sparse

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
            molgrp = self.root_item.data_file[item.name]
            _context_mol(item,treeview,position,molgrp)

        if _type == 'sparse_matrix':
            _context_sparse(item,treeview,position)

        if _type == 'epoch':
            _context_epoch(item,treeview,position)

        if _type == 'losses':
            _context_losses(item,treeview,position)

    except Exception as inst:
        print(type(inst))
        print(inst)
        return

def _context_mol(item,treeview,position,molgrp):

    menu = QtWidgets.QMenu()
    actions = {}
    list_operations = ['Load in PyMol','Load in VMD','PDB2SQL']

    for operation in list_operations:
        actions[operation] = menu.addAction(operation)
    action = menu.exec_(treeview.viewport().mapToGlobal(position))

    if action == actions['Load in VMD']:
        _,cplx_name,mol_name = item.name.split('/')
        viztools.create3Ddata(mol_name,molgrp)
        viztools.launchVMD(mol_name)

    if action == actions['Load in PyMol']:
        _,cplx_name,mol_name = item.name.split('/')
        viztools.create3Ddata(mol_name,molgrp)
        viztools.launchPyMol(mol_name)

    if action == actions['PDB2SQL']:
        _,cplx_name,mol_name = item.name.split('/')
        db = pdb2sql(molgrp['complex'].value)
        treeview.emitDict.emit({'sql_' + item.basename: db})

def _context_sparse(item,treeview,position):

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

def _context_epoch(item,treeview,position):

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

def _context_losses(item,treeview,position):

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


