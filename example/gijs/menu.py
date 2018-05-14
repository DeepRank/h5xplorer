from PyQt5 import QtWidgets
from h5xplorer.menu_tools import *

def context_menu(self, treeview, position):

    """Generate a right-click menu for the items"""

    all_item = get_current_item(self,treeview,single=False)

    if len(all_item) == 1:

        item = all_item[0]

        list_operations = ['Print attrs','-','Plot Hist', 'Plot 2D']
        action,actions = get_actions(treeview,position,list_operations)

        if action == actions['Print attrs']:
            send_dict_to_console(self,item,treeview)
            #print_attributes(self,item,treeview)

        if action == actions['Plot Hist']:
            plot_histogram(self,item,treeview)

        if action == actions['Plot 2D']:
            plot2d(self,item,treeview)

    elif len(all_item) == 2:

        item0,item1 = all_item

        list_operations = ['Plot Scatter','Plot Line']
        action,actions = get_actions(treeview,position,list_operations)

        if action == actions['Plot Scatter']:
            plot1D(self,item0,item1,treeview,plot='scatter')

        if action == actions['Plot Line']:
            plot1D(self,item0,item1,treeview,plot='line')