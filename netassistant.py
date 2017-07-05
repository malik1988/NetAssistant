#coding: utf-8

from PyQt5 import uic
import os

uipath, uiname = os.path.split(os.path.realpath(__file__))
uiname = uiname.replace('.py', '.ui')
uifile = os.path.join(uipath, uiname)
ui_mainwindow, qtbaseclass = uic.loadUiType(uifile)


class NetAssistant(ui_mainwindow, qtbaseclass):

    connected = False  # 连接状态

    def __init__(self):
        ui_mainwindow.__init__(self)
        qtbaseclass.__init__(self)
        self.setupUi(self)
        for x in ('TCP Client', 'TCP Server', 'UDP'):
            self.comboBox_protocol.addItem(x)

        for x in ('127.0.0.1', '0.0.0.0'):
            self.comboBox_local.addItem(x)

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

        self.connected = not self.connected

        # 下一个状态，与当期状态取反（用于显示提示信息）
        next_state = not self.connected
        dict_next = {True: '打开', False: '关闭'}
        self.pushButton_connect.setText(dict_next[next_state])

        self.comboBox_protocol.setEnabled(next_state)
        self.comboBox_local.setEnabled(next_state)
        self.comboBox_target.setEnabled(next_state)
