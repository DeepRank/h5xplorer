#!/usr/bin/env python

from h5xplorer.h5xplorer import h5xplorer
import menu

app = h5xplorer(menu.context_menu,extended_selection=True)