from PyQt5 import QtWidgets
from h5xplorer.menu_tools import *
from h5xplorer.menu_plot import *
import numpy as np

def context_menu(self, treeview, position):

    """Generate a right-click menu for the items"""

    item = get_current_item(self,treeview,single=True)

    data = get_group_data(get_current_hdf5_group(self,item))

    if data is None:
        list_operations = ['Print attrs','-','Eigenvalue','Coupling']

    elif data.ndim == 1:
        list_operations = ['Print attrs','-','Plot Hist', 'Plot Line']

    elif data.ndim == 2:
        list_operations = ['Print attrs','-','Plot Hist', 'Plot Map']

    else:
        list_operations = ['Print attrs']

    action,actions = get_actions(treeview,position,list_operations)

    if action == actions['Print attrs']:
        send_dict_to_console(self,item,treeview)

    if 'Plot Hist' in actions:
        if action == actions['Plot Hist']:
            plot_histogram(self,item,treeview)

    if 'Plot Line' in actions:
        if action == actions['Plot Line']:
            plot_line(self,item,treeview)

    if 'Plot Map' in actions:
        if action == actions['Plot Map']:
            plot2d(self,item,treeview)

    if 'Eigenvalue' in actions:
        if action == actions['Eigenvalue']:
            plot_eigen(self,item,treeview)

    if 'Coupling' in actions:
        if action == actions['Coupling']:
            plot_coupling(self,item,treeview)

def plot_eigen(self,item,treeview):

    indexes = get_user_values(['indexes'],vartypes='str',windowtitle='Enter indexes')[0]
    indexes = indexes.split(',')

    ind_values = []
    for ind in indexes:
        if '-' in ind:
            ind_values += list(range(int(ind.split('-')[0]),int(ind.split('-')[-1])+1))
        elif ind == 'all':
            ind_values += [ind]
        else:
            ind_values += int(ind)

    grp = get_current_hdf5_group(self,item)
    point_groups = list(filter(lambda x: 'point_' in x,list(grp.keys())))
    selected_values = []
    for subgroup in point_groups:
        values = grp[subgroup + '/cp2k/mo/eigenvalues'].value
        if ind_values == ['all']:
            selected_values.append(values)
        else:
            selected_values.append(values[ind_values])
    selected_values = np.array(selected_values)

    data_dict = {'_data':selected_values}
    treeview.emitDict.emit(data_dict)

    data_dict = {'exec_cmd':'plot_time_series(_data)'}
    treeview.emitDict.emit(data_dict)

def plot_coupling(self,item,treeview):

    indexes = get_user_values(['index1','index2'],vartypes='str',windowtitle='Enter indexes')

    both_ind_val = []
    for index in indexes:
        index = index.split()
        ind_values = []
        for ind in index:
            if '-' in ind:
                ind_values += list(range(int(ind.split('-')[0]),int(ind.split('-')[-1])+1))
            elif ind == 'all':
                ind_values += [ind]
            else:
                ind_values += [int(ind)]
        both_ind_val.append(ind_values)

    grp = get_current_hdf5_group(self,item)
    point_groups = list(filter(lambda x: 'coupling_' in x,list(grp.keys())))
    selected_values = []
    for subgroup in point_groups:

        values = grp[subgroup].value
        norb = values.shape[0]

        for i in range(2):
            if both_ind_val[i] == ['all']:
                both_ind_val[i] = list(range(norb))

        selected_values.append(values[np.ix_(both_ind_val[0],both_ind_val[1])].flatten())
    selected_values = np.array(selected_values)

    data_dict = {'_data':selected_values}
    treeview.emitDict.emit(data_dict)

    data_dict = {'exec_cmd':'plot_time_series(_data)'}
    treeview.emitDict.emit(data_dict)
