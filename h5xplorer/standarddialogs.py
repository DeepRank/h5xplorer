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

    def __init__(self, varnames, window_name = 'Enter Values', parent=None):
        super(Dialog, self).__init__(parent)

        frameStyle = QFrame.Sunken | QFrame.Panel

        self.varnames = varnames
        self.Label,self.Button,self.values = {},{},{}

        for name in varnames:
            self.Label[name] = QLabel()
            self.Label[name].setFrameStyle(frameStyle)
            self.Button[name] = QPushButton(name)

        self.closeButton = QPushButton("OK")


        for name in varnames:
            self.Button[name].clicked.connect(partial(self.setValue, name))
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


    def setValue(self,name):
        """Set the value of the variable

        Args:
            name (str): variable name
        """
        d, ok = QInputDialog.getDouble(self, "QInputDialog.getDouble()",
                "Amount:", 37.56, -10000, 10000, 2)
        if ok:
            self.Label[name].setText("$%g" % d)
            self.values[name] = d

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
