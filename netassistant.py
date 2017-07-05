#coding: utf-8
from PyQt5.QtWidgets import QMessageBox, QComboBox
from PyQt5 import QtCore
from PyQt5 import uic
import os
import socket

import re

uipath, uiname = os.path.split(os.path.realpath(__file__))
uiname = uiname.replace('.py', '.ui')
uifile = os.path.join(uipath, uiname)
ui_mainwindow, qtbaseclass = uic.loadUiType(uifile)


class NetAssistant(ui_mainwindow, qtbaseclass):

    connected = False  # 连接状态
    proto = None  # 记录当前协议类型
    sock = None  # 记录当前连接的socket
    addr_local = None  # 本地主机地址
    addr_remote = None  # 远程主机地址

    def __init__(self):
        ui_mainwindow.__init__(self)
        qtbaseclass.__init__(self)
        self.setupUi(self)
        self.comboBox_protocol.addItems(['TCP Client', 'TCP Server', 'UDP'])
        self.comboBox_local.addItems(['127.0.0.1', '0.0.0.0'])

    def data_recevie(self):
        while self.sock.bytesAvailable()>0:
            self.textBrowser.append(self.sock.read())

    def slot_proto_change(self, proto):
        '''协议类型更改'''

        if proto == 'TCP Client':
            self.label_local.setText(u'(2)本地主机地址')
            self.label_target.setText(u'(3)远程主机地址')
        elif proto == 'TCP Server':
            self.label_local.setText(u'(2)本地主机地址')
            self.label_target.setText(u'(3)本地主机端口')
        else:
            self.label_local.setText(u'(2)本地主机地址')
            self.label_target.setText(u'(3)本地主机端口')

    def slot_connect(self):
        '''打开（连接）按钮按下'''

        # 下一个状态，与当期状态取反（用于显示提示信息）
        next_state = not self.connected

        if next_state:
            if self.sock_connect():
                self.connected = next_state
                next_state = not self.connected
        else:
            if self.sock_disconnect():
                self.connected = next_state
                next_state = not self.connected

        dict_next = {True: '打开', False: '关闭'}
        self.pushButton_connect.setText(dict_next[next_state])

        self.comboBox_protocol.setEnabled(next_state)
        self.comboBox_local.setEnabled(next_state)
        self.comboBox_target.setEnabled(next_state)

    def sock_connect(self):
        self.proto = self.comboBox_protocol.currentText()
        addr = self.comboBox_target.currentText()
        if self.proto == 'TCP Client':
            try:
                if ':' in addr:
                    ip, port = addr.split(':')
                    address = (ip, int(port))

                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect(address)
                #添加成功连接的记录，方便下次直接下拉
                self.comboBox_target.addItem(addr)
                # self.connect(self.sock, QtCore.SIGNAL('readyRead()'), self.data_recevie)
            except Exception as e:
                self.sock = None
                QMessageBox.critical(self, '错误', '地址:%r ，连接失败！' % addr)
        return self.sock != None

    def sock_disconnect(self):
        if self.sock:
            try:
                self.sock.close()
                self.sock = None
            except Exception as e:
                print(e)
        return self.sock == None

    def slot_local_addr_change(self):
        '''本地主机地址更改'''
        addr = self.comboBox_local.currentText()
        if re.match(
                r'(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)\.(25[0-5]|2[0-4]\d|[0-1]\d{2}|[1-9]?\d)',
                addr):
            self.addr_local = addr
        else:
            QMessageBox.show(self, 'errr', 'addr=%s not IP ' % addr)

    def slot_send(self):
        if self.sock:
            text = self.textEdit_send.toPlainText()
            if text:
                try:
                    b = bytes(text, encoding='utf-8')
                    self.sock.send(b)
                except Exception as e:
                    print(e)
            else:
                QMessageBox.critical(self, '错误', '数据为空！')
        else:
            QMessageBox.critical(self, '错误', '请先打开连接！')
