from PyQt5 import QtWidgets
def get_current_item(self,treeview,single=False):

    items = [self._index_to_item(index) for index in treeview.selectedIndexes()]

    if single:
        if len(items)!=1:
            return 
        items = items[0]
    return items

def get_current_hdf5_group(self,item):
    return self.root_item.data_file[item.name]

def get_group_data(group):
    try:
        return group.value
    except Exception as ex:
        print(ex)
        return None

def get_actions(treeview,position,list_action):

    menu = QtWidgets.QMenu()
    actions = {}

    for operation in list_action:
        actions[operation] = menu.addAction(operation)
    selected_action = menu.exec_(treeview.viewport().mapToGlobal(position))
    return selected_action,actions


def send_dict_to_console(self,item,treeview):

    grp = get_current_hdf5_group(self,item)
    data = {'attrs':list(grp.attrs)}
    treeview.emitDict.emit(data)

# def print_attributes(self,item,treeview):
#     grp = get_current_hdf5_group(self,item)
#     attrs = list(grp.attrs)
#     val = list(grp.attrs.values())
#     print(attrs)
#     print(val)
#     data = {}
#     for a in attrs:
#         data[a] = 0
#     treeview.emitDict.emit(data)

def plot_histogram(self,item,treeview):

    grp = get_current_hdf5_group(self,item)
    value = get_group_data(grp)

    if value is not None:
        data_dict = {'value':value}
        treeview.emitDict.emit(data_dict)

        cmd = "%matplotlib inline\nimport matplotlib.pyplot as plt\nplt.hist(value,10)\nplt.show()\n"
        data_dict = {'exec_cmd':cmd}
        treeview.emitDict.emit(data_dict)

def plot1D(self,item0,item1,treeview,plot='line'):

    grp0 = get_current_hdf5_group(self,item0)
    grp1 = get_current_hdf5_group(self,item1)

    x = get_group_data(grp0)
    y = get_group_data(grp1)

    xlabel = item0.basename
    ylabel = item1.basename

    if x.ndim != 1 or y.ndim != 1 or x.shape!=y.shape:
        return

    data_dict = {'x':x,'y':y}
    treeview.emitDict.emit(data_dict)

    data_dict = {}
    cmd  = "%matplotlib inline\nimport matplotlib.pyplot as plt\n"
    cmd += "fig,ax = plt.subplots()\n"

    if plot == 'scatter':
        cmd += "ax.scatter(x,y)\n"
    elif plot == 'line':
        cmd += "ax.plot(x,y)\n"

    cmd += "ax.set_xlabel('%s')\n" %xlabel
    cmd += "ax.set_ylabel('%s')\n" %ylabel
    cmd += "plt.show()\n"
    data_dict['exec_cmd'] = cmd
    treeview.emitDict.emit(data_dict)

def plot2d(self,item,treeview):

    grp = get_current_hdf5_group(self,item)
    data = get_group_data(grp)

    if data.ndim != 2:
        return

    data_dict = {'map':data}
    treeview.emitDict.emit(data_dict)

    data_dict = {}
    cmd  = "%matplotlib inline\nimport matplotlib.pyplot as plt\n"
    cmd += "plt.imshow(map)\n"
    cmd += "plt.show()\n"
    data_dict['exec_cmd'] = cmd
    treeview.emitDict.emit(data_dict)