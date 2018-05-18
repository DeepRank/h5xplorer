import sys
from functools import partial
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtWidgets import (QApplication, QCheckBox, QColorDialog, QDialog,
        QErrorMessage, QFileDialog, QFontDialog, QFrame, QGridLayout,
        QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton)


class Dialog(QDialog):

    """Class to generate an user-defined input box

    Example

    >>> dialog = Dialog(varnames)
    >>> dialog.exec_()
    >>> return dialog.returnValues()

    Attributes:
        closeButton (QPushButton): Push butto to close the dialog box
        errorMessageDialog (TYPE): Description
        native (QCheckBox): Description
        varnames (list): Name of the variable we want to  input
    """

    def __init__(self, varnames, vartypes = 'float', window_name = 'Enter Values', parent=None):
        super(Dialog, self).__init__(parent)

        frameStyle = QFrame.Sunken | QFrame.Panel

        self.varnames = varnames
        self.vartypes = vartypes
        if not isinstance(self.vartypes,list):
            self.vartypes = [vartypes]*len(self.varnames)


        self.Label,self.Button,self.values = {},{},{}

        for name in varnames:
            self.Label[name] = QLabel()
            self.Label[name].setFrameStyle(frameStyle)
            self.Button[name] = QPushButton(name)

        self.closeButton = QPushButton("OK")


        for name,vtype in zip(self.varnames,self.vartypes):
            self.Button[name].clicked.connect(partial(self.setValue, name,vtype))
        self.closeButton.clicked.connect(self.close)

        self.native = QCheckBox()
        self.native.setText("Use native file dialog.")
        self.native.setChecked(True)
        if sys.platform not in ("win32", "darwin"):
            self.native.hide()

        layout = QGridLayout()
        layout.setColumnStretch(1, 1)
        layout.setColumnMinimumWidth(1, 250)

        for i,name in enumerate(varnames):
            layout.addWidget(self.Button[name], i, 0)
            layout.addWidget(self.Label[name], i, 1)

        layout.addWidget(self.closeButton, len(varnames), 1)
        self.setLayout(layout)
        self.setWindowTitle(window_name)


    def setValue(self,name,vtype):
        """Set the value of the variable

        Args:
            name (str): variable name
            type (str): variable type
        """
        if vtype == 'float':
            d, ok = QInputDialog.getDouble(self, "Get Double",
                    "Value:", 37.56, -10000, 10000, 2)
            if ok:
                self.Label[name].setText("$%g" % d)
                self.values[name] = d

        elif vtype == 'str':
            text, ok = QInputDialog.getText(self, "Get String",
                    "Value:", QLineEdit.Normal, '')
            if ok and text != '':
                self.Label[name].setText(text)
                self.values[name] = text

        elif vtype == 'int':
            i, ok = QInputDialog.getInt(self, "Get Integer",
                    "Value:", 25, 0, 100, 1)
            if ok:
                self.Label[name].setText("%d%%" % i)
                self.values[name] = i

    def returnValues(self):
        """Return the values of all the variables

        Returns:
            list: The values of the variables
        """
        return [self.values[name] for name in self.varnames]




# class Error(QErrorMessage):

#     """Errorbox
#     """

#     def __init__(self, text, parent=None):
#         super(Error, self).__init__(parent)
#         error = QMessageBox.information(self,text)

# def show_error_message(text):
#     errorbox = Error(text)
