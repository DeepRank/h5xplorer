from PyQt5 import QtWidgets
from h5xplorer.menu_tools import *

#from standarddialogs import Dialog
import numpy as np

def context_menu(self, treeview, position):

    """Generate a right-click menu for the items"""

    all_item = get_current_item(self,treeview,single=False)

    if len(all_item) == 1:

        item = all_item[0]
        grp = get_current_hdf5_group(self,item)

        if 'time' not in grp:
            return
        else:
            timestep = grp['time'].value
            nstep = len(timestep)

        list_operations = ['Print attrs','Time Step','Time Evol']
        list_subop = [[],[str(i) for i in range(nstep)],[]]

        action, actions = get_multilevel_actions(treeview,position,list_operations,list_subop)

        if action == actions['Print attrs']:
            send_dict_to_console(self,item,treeview)

        for istep in range(nstep):
            if action == actions[('Time Step',str(istep))]:
                selected_time = istep
                plot_slice(self,item,treeview,selected_time)

        if action == actions['Time Evol']:
            plot_time_serie(self,item,treeview)


def plot_slice(self,item,treeview,selected_time):

    grp = get_current_hdf5_group(self,item)
    value = grp['discharge'].value
    lon = grp['lon'].value
    lat = grp['lat'].value
    data = value[selected_time,...]
    data_dict = {'_map':data,'_lon':lon,'_lat':lat}
    treeview.emitDict.emit(data_dict)

    data_dict = {}
    cmd  = "%matplotlib inline\nimport matplotlib.pyplot as plt\n"
    #cmd += 'plt.subplot(111, projection="aitoff")\n'
    cmd += "plt.imshow(_map)\n"
    #cmd += 'plt.grid(True)\n'
    cmd += "plt.show()\n"
    data_dict['exec_cmd'] = cmd
    treeview.emitDict.emit(data_dict)


def plot_time_serie(self,item,treeview):

    select_lat,select_lon = get_user_values(['Lattitute','Longitude'],windowtitle='Enter Position')

    grp = get_current_hdf5_group(self,item)
    value = grp['discharge'].value
    lon = grp['lon'].value
    lat = grp['lat'].value
    time = grp['time'].value

    index_lat = np.argmin(np.abs(lat-select_lat))
    index_lon = np.argmin(np.abs(lon-select_lon))

    data = value[:,index_lat,index_lon].reshape(-1)
    data_dict = {'_data':data,'_time':time}
    treeview.emitDict.emit(data_dict)

    data_dict = {}
    cmd  = "%matplotlib inline\nimport matplotlib.pyplot as plt\n"
    cmd += "plt.plot(_time,_data)\n"
    cmd += "plt.xlabel('Time')\n"
    cmd += "plt.ylabel('Discharge')\n"
    cmd += "plt.show()\n"
    data_dict['exec_cmd'] = cmd
    treeview.emitDict.emit(data_dict)

