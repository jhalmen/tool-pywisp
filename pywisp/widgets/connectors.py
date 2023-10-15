# -*- coding: utf-8 -*-
import os
import PyQt5.QtCore as Qcore
import PyQt5.QtGui as Qgui
import PyQt5.QtWidgets as Qw
import serial.tools.list_ports as serial_ports
from pywisp import connection as conn
from pywisp import registry

__all__ = ["ConnectionMenu", "Connector", "IPDialog", "TCP", "UDP", "Serial"]

class Connector(Qw.QDialog):
    """
    base class for Qt Widget for creating connections
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent)
        self.setWindowIcon(
            Qgui.QIcon(os.path.dirname(__file__)+"/../resources/icons/icon.svg")
        )

class IPDialog(Connector):
    """
    Qt Dialog for creating IP based connections
    """

    def __init__(self, parent, ip="127.0.0.1", port=45670):
        super().__init__(parent)

        ipRange = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"  # Part of the regular expression
        # regular expression
        ipRegex = Qcore.QRegExp("^" + ipRange + "\\." + ipRange + "\\." + ipRange + "\\." + ipRange + "$")
        ipValidator = Qgui.QRegExpValidator(ipRegex, self)

        mainLayout = Qw.QVBoxLayout(self)

        self.ipData = Qw.QLineEdit(self)
        self.ipData.setText(str(ip))
        self.ipData.setValidator(ipValidator)

        self.portData = Qw.QLineEdit(self)
        self.portData.setText(str(port))
        self.portData.setValidator(Qgui.QIntValidator(0, 65535, self))

        horizonalLayout = Qw.QHBoxLayout()

        horizonalLayout.addWidget(self.ipData)
        horizonalLayout.addWidget(self.portData)
        mainLayout.addLayout(horizonalLayout)

        # OK and Cancel buttons
        buttons = Qw.QDialogButtonBox(
            Qw.QDialogButtonBox.Ok | Qw.QDialogButtonBox.Cancel,
            Qcore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        mainLayout.addWidget(buttons)
        self.data = None
    def accept(self):
        self.data =  {'ip':self.ipData.text(), 'port':int(self.portData.text())}
        super().accept()
    def reject(self):
        if self.data:
            self.ipData.setText(self.data['ip'])
            self.portData.setText(str(self.data['port']))
        super().reject()

class TCP(IPDialog):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

    def accept(self):
        super().accept()
        self.connection = conn.Tcp(parent=self.parent(), **self.data)

class UDP(IPDialog):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
    def accept(self):
        super().accept()
        self.connection = conn.Udp(parent=self.parent(), **self.data)

class Serial(Connector):
    def __init__(self, parent, port='', baud='115200'):
        super().__init__(parent)
        self.data = (port, baud)
        ports = [p.device for p in serial_ports.comports()]
        bauds = ['1200', '2400', '4800', '9600', '14400', '19200', '28800',
                 '38400', '57600', '115200', '125000', '250000', '500000']
        vlayout = Qw.QVBoxLayout(self)
        hlayout = Qw.QHBoxLayout()
        vlayout.addLayout(hlayout)

        self.ports = Qw.QComboBox()
        self.ports.addItems(ports)
        self.bauds = Qw.QComboBox()
        self.bauds.addItems(bauds)
        hlayout.addWidget(self.ports)
        hlayout.addWidget(self.bauds)
        # OK and Cancel buttons
        buttons = Qw.QDialogButtonBox(
            Qw.QDialogButtonBox.Ok | Qw.QDialogButtonBox.Cancel,
            Qcore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        vlayout.addWidget(buttons)
        self.reset()
    def reset(self):
        self.ports.setCurrentText(self.data[0])
        self.bauds.setCurrentText(self.data[1])
    def accept(self):
        super().accept()
        self.data = (self.ports.currentText(), self.bauds.currentText())
        self.connection = conn.Serial(self.data[0], self.data[1], parent=self.parent())
    def reject(self):
        super().reject()
        self.reset()

class ConnectionMenu(Qw.QMenu):
    """
    Menu for creating and managing connections
    """
    def __init__(self, parent, title='&Connections', **kwargs):
        super().__init__(parent, title=title, **kwargs)
        self.connectors = []
        self.logger = parent._logger

    def showEvent(self, qshowevent):
        self.clear()
        try:
            for c in registry.getRegisteredConnectors():
                act = self.addAction(f'add {c.__name__} connection')
                act.triggered.connect(lambda _, conn=c: self.new(conn))
            self.addSeparator()
            for c in self.connectors:
                sub = self.addMenu(f'{type(c)}')
                act = sub.addAction('edit')
                act.triggered.connect(c.exec)
                rm = sub.addAction('remove')
                rm.triggered.connect(lambda _, conn=c: self.remove(conn))
        except Exception as e:
            self.logger.error(f"Connector error {type(e)} : '{e}'")

    def new(self, connector):
        conn = connector(self.parent())
        if conn.exec():
            self.connectors.append(conn)

    def remove(self, connector):
        if connector.connection.connected:
            connector.connection.disconnect()
        self.connectors.remove(connector)

