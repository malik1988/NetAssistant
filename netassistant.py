#coding: utf-8
from PyQt5.QtWidgets import QMessageBox, QComboBox
from PyQt5 import QtCore
from PyQt5 import uic
import os
from datetime import datetime

from PyQt5.QtNetwork import QTcpSocket, QTcpServer, QUdpSocket, QHostAddress
import re

uipath, uiname = os.path.split(os.path.realpath(__file__))
uiname = uiname.replace('.py', '.ui')
uifile = os.path.join(uipath, uiname)
ui_mainwindow, qtbaseclass = uic.loadUiType(uifile)


class NetAssistant(ui_mainwindow, qtbaseclass):

    connected = False  # 连接状态
    proto = None  # 记录当前协议类型
    addr_local = None  # 本地主机地址
    addr_remote = None  # 远程主机地址
    hex_view = False  # 十六进制显示标志
    time_view = False  # 显示接收时间标志
    net = None  # 当前网络连接 NetHelper类型

    def __init__(self):
        ui_mainwindow.__init__(self)
        qtbaseclass.__init__(self)
        self.setupUi(self)
        self.comboBox_protocol.addItems(['TCP Client', 'TCP Server', 'UDP'])
        self.comboBox_local.addItems(['127.0.0.1', '0.0.0.0'])

    def data_recevie(self):
        if self.net:
            while self.net.bytesAvailable() > 0:
                data = self.net.readAll()  # Qbytearray类型
                if self.hex_view:
                    # 转换成十六进制数
                    data = data.toHex()
                data = bytearray(data)  # 转成python的bytes类型，方便处理
                try:
                    s = data.decode('gbk')
                    if self.time_view:
                        # 显示接收时间
                        now = datetime.now()
                        s = '[%s] ' % now.strftime('%Y-%m-%d %H:%M:%S,%f') + s

                    if self.hex_view:
                        s = s.upper()

                    self.textBrowser.append(s)
                except Exception as e:
                    QMessageBox.critical(self, '错误', '数据编码有误！可尝试十六进制显示。')

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
        '''连接打开'''
        self.proto = self.comboBox_protocol.currentText()
        if self.proto == 'TCP Client':
            try:
                #远程地址： ip:port
                addr = self.comboBox_target.currentText()
                if ':' in addr:
                    ip, port = addr.split(':')
                    # address = (ip, int(port))
                    port = int(port)

                self.net = NetHelper(sock_type='TCP Client', ip=ip, port=port)

                #添加成功连接的记录，方便下次直接下拉
                self.comboBox_target.addItem(addr)
            except Exception as e:
                self.sock = None
                QMessageBox.critical(self, '错误', '地址:%r ，连接失败！' % addr)
        elif self.proto == 'UDP':
            # UDP
            ip = self.comboBox_local.currentText()
            port = self.comboBox_target.currentText()
            try:
                port = int(port)
                self.net = NetHelper(sock_type='UDP', ip=ip, port=port)
            except Exception as e:
                pass
                self.net = None
        elif self.proto=='TCP Server':
            ip = self.comboBox_local.currentText()
            port = self.comboBox_target.currentText()
            try:
                port=int(port)
                self.net=NetHelper(sock_type='TCP Server',ip=ip,port=port)
            except Exception as e:
                pass
                self.net = None
            
        else:
            pass

        if self.net:
            # 绑定接收
            self.net.readyReadConnect(self.data_recevie)

        return self.net != None

    def sock_disconnect(self):
        '''连接关闭'''
        if self.net:
            try:
                self.net.close()
                self.net = None
            except Exception as e:
                print(e)
        return self.net == None

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
        '''发送按钮按下事件'''
        if self.net:
            text = self.textEdit_send.toPlainText()
            if text:
                try:
                    b = bytes(text, encoding='utf-8')
                    if self.proto == 'UDP':
                        host = self.comboBox_host.currentText()
                        ip_host, port_host = host.split(':')
                        port_host = int(port_host)
                        self.net.send(b, ip_host=ip_host, port_host=port_host)
                    else:
                        self.net.send(b)
                except Exception as e:
                    print(e)
            else:
                QMessageBox.critical(self, '错误', '数据为空！')
        else:
            QMessageBox.critical(self, '错误', '请先打开连接！')

    def slot_hex_view_change(self, state):
        '''十六进制显示更改'''
        self.hex_view = True if state else False

    def slot_time_view_change(self, state):
        '''显示接收时间更改'''
        self.time_view = True if state else False

    def slot_clear_view(self):
        '''清除显示'''
        self.textBrowser.clear()

    def slot_save_view(self):
        '''保存显示'''
        pass


class NetHelper(object):
    '''TCP/UDP 统一接口类'''

    socket_tcp_client = QTcpSocket()
    socket_tcp_server = QTcpServer()
    socket_udp = QUdpSocket()

    sock = None
    sock_type = None
    ip = None
    port = None

    list_clients=list()

    # ip_host = None  # UDP 使用，远程IP地址
    # port_host = None  # UDP使用，远程端口

    def __init__(self, **kwargs):
        self.open(**kwargs)

    def open(self, sock_type='TCP Client', ip='127.0.0.1', port=2007):
        '''打开网络设备，建立连接
        @sock_type:
            'TCP Client','TCP Server','UDP'
        '''
        self.sock_type = sock_type
        self.ip = ip
        self.port = port

        if sock_type == 'TCP Client':
            self.socket_tcp_client.connectToHost(ip, port)
            self.sock = self.socket_tcp_client
        elif sock_type == 'TCP Server':
            self.socket_tcp_server.listen(QHostAddress(ip), port)
            self.socket_tcp_server.newConnection.connect(self.listen)
            self.sock = self.socket_tcp_server
            
        elif sock_type == 'UDP':
            self.socket_udp.bind(QHostAddress(self.ip), self.port)
            self.sock = self.socket_udp
        else:
            print('Unkonw sock_type=%r' % sock_type)

    def listen(self):
        self.list_clients.append(self.sock.nextPendingConnection())

    def close(self):
        '''关闭网络设备，断开连接'''
        if self.sock:
            self.sock.close()
            self.sock = None

    def bytesAvailable(self):
        '''获取可读取数据长度'''
        if self.sock_type == 'TCP Client':
            return self.sock.bytesAvailable()
        elif self.sock_type == 'TCP Server':
            pass
        elif self.sock_type == 'UDP':
            return self.sock.pendingDatagramSize()
        else:
            pass

    def readAll(self):
        if self.sock_type == 'TCP Client':
            return self.sock.readAll()
        elif self.sock_type == 'TCP Server':
            pass
        elif self.sock_type == 'UDP':
            data, host, port = self.sock.readDatagram(self.port)
            data = QtCore.QByteArray(data)
            return data
        else:
            pass

    def send(self, data, ip_host=None, port_host=None):
        '''发送数据'''
        if self.sock_type == 'TCP Client':
            return self.sock.write(data)
        elif self.sock_type == 'UDP':
            return self.sock.writeDatagram(data,
                                           QHostAddress(ip_host), port_host)
        elif self.sock_type == 'TCP Server':
            for client in self.list_clients:
                print(client)
        else:
            pass

    def readyReadConnect(self, func):
        if self.sock_type == 'TCP Client':
            return self.sock.readyRead.connect(func)
        elif self.sock_type == 'TCP Server':
            pass
        elif self.sock_type == 'UDP':
            return self.sock.readyRead.connect(func)
        else:
            pass


if __name__ == '__main__':
    net = NetHelper(sock_type='UDP', ip='127.0.0.1', port=2007)
    s = 'test'
    data = bytes(s, encoding='utf-8')
    net.send(data)
