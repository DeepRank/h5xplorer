from PyQt5 import QtWidgets
from h5xplorer.menu_tools import *
from h5xplorer.menu_plot import *

def default_context_menu(self, treeview, position):

    """Generate a right-click menu for the items"""

    all_item = get_current_item(self,treeview,single=False)

    if len(all_item) == 1:

        item = all_item[0]
        data = get_group_data(get_current_hdf5_group(self,item))

        if data is None:
            list_operations = ['Print attrs']

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

    elif len(all_item) == 2:

        item0,item1 = all_item

        list_operations = ['Plot Scatter','Plot Line']
        action,actions = get_actions(treeview,position,list_operations)

        if action == actions['Plot Scatter']:
            plot1D(self,item0,item1,treeview,plot='scatter')

        if action == actions['Plot Line']:
            plot1D(self,item0,item1,treeview,plot='line')