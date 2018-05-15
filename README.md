# h5xplorer


[![Documentation Status](https://readthedocs.org/projects/h5xplorer/badge/?version=latest)](http://h5xplorer.readthedocs.io/?badge=latest)


**Customizable Framework for the Creation of HDF5 Browsers**

## Instalation

```
git clone https://github.com/DeepRank/h5xplorer
pip install ./
```

## Example


![alt-text](./h5x.gif)

For example the main file can look like that

```python
from h5xplorer.h5xplorer import h5xplorer
import menu

app = h5xplorer(menu.context_menu, extended_selection=True)
```

All the menus are defined in a separte python file here called ```menu.py```

```python
from PyQt5 import QtWidgets
from h5xplorer.menu_tools import *

def context_menu(self, treeview, position):

    """Generate a right-click menu for the items"""

    all_item = get_current_item(self,treeview,single=False)

    if len(all_item) == 1:

        item = all_item[0]

        list_operations = ['Print attrs','Plot Hist', 'Plot 2D']
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

```
