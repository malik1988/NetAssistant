#coding: utf-8
from PyQt5.QtWidgets import QMessageBox, QComboBox, QFileDialog
from PyQt5 import QtCore
from PyQt5 import uic
import os
from datetime import datetime
from binascii import a2b_hex, b2a_hex

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
    net = None  # 当前网络连接 NetHelper类
    hex_send = None  # 十六进制发送标志
    save_file = None  # 接收转向文件标志
    save_file_name = None  # 接收转向文件名（全路径）

    client_list = []  # 记录所有连接的TCP 客户端

    def __init__(self):
        ui_mainwindow.__init__(self)
        qtbaseclass.__init__(self)
        self.setupUi(self)
        self.comboBox_protocol.addItems(['TCP Client', 'TCP Server', 'UDP'])
        self.comboBox_local.addItems(['127.0.0.1', '0.0.0.0'])

    def __view(self, data, prefix=''):
        '''显示数据
        @data:
            需要显示的原始数据（binary）
        @prefix:
            需要显示的前缀（string）
        '''
        if self.hex_view:
            # 转换成十六进制数
            data = data.toHex()
        if self.save_file and self.save_file_name:
            #接收转向文件
            # with open(self.save_file_name, 'wb') as f:
            #     f.write(data)
            pass
        data = bytearray(data)  # 转成python的bytes类型，方便处理
        try:
            s = data.decode('gbk')
            if self.time_view:
                # 显示接收时间
                now = datetime.now()
                s = '[%s] ' % now.strftime('%Y-%m-%d %H:%M:%S,%f') + s

            if self.hex_view:
                s = s.upper()
            self.textBrowser.append(prefix + s)
        except Exception as e:
            QMessageBox.critical(self, '错误', '数据编码有误！可尝试十六进制显示。')

    def data_recevie(self):
        '''数据接收（TCP Client/UDP）'''
        if self.net:
            while self.net.bytesAvailable() > 0:
                data, host = self.net.readAll()  # Qbytearray类型
                if host:
                    ip = host[0].toString()
                    port = host[1]
                    host = '[From %s:%s] ' % (ip, port)
                else:
                    host = ''

                self.__view(data, prefix=host)

    def slot_proto_change(self, proto):
        '''协议类型更改'''
        if proto == 'TCP Server':
            self.label_host.setText(u'客户端：')
            self.comboBox_host.addItem(u'所有连接')
            self.pushButton_host.setText(u'断开连接')
        else:
            self.label_host.setText(u'远程主机：')
            self.comboBox_host.clear()
            self.pushButton_host.setText(u'清除主机')

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
        self.comboBox_port.setEnabled(next_state)

    def sock_connect(self):
        '''连接打开'''
        self.proto = self.comboBox_protocol.currentText()
        ip = self.comboBox_local.currentText()
        port = self.comboBox_port.currentText()

        try:
            port = int(port)
            if self.proto == 'TCP Client':
                self.net = NetHelper(sock_type='TCP Client', ip=ip, port=port)
            elif self.proto == 'UDP':
                self.net = NetHelper(sock_type='UDP', ip=ip, port=port)
            elif self.proto == 'TCP Server':
                self.net = NetHelper(sock_type='TCP Server', ip=ip, port=port)
                # 绑定客户端连接消息
                self.net.sock.newConnection.connect(
                    self.tcpServer_onConnection)
            else:
                pass
        except:  # Exception as e:
            self.sock = None
            QMessageBox.critical(self, '错误', '地址:%s，端口:%s ，连接失败！' % (ip, port))

        if self.net:
            # 绑定接收
            self.net.readyReadConnect(self.data_recevie)

        return self.net != None

    def sock_disconnect(self):
        '''连接关闭'''
        if self.net:
            try:
                if self.proto == 'TCP Server':
                    # 断开所有客户端，并清除client_list
                    l = self.client_list.copy()
                    try:
                        for c in l:
                            # 调用会触发 disconnect，其中包含删除self.client_list中数据
                            c.close()
                    except:
                        pass
                    self.client_list.clear()

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

    def __send(self, b):
        '''发送数据
        @b:
            binary数据
        '''
        if self.proto == 'UDP':
            host = self.comboBox_host.currentText()
            if not host:
                raise Exception("请输入远程主机地址和端口，例如: 127.0.0.1:2007 。")
            ip_host, port_host = host.split(':')
            port_host = int(port_host)
            self.net.send(b, ip_host=ip_host, port_host=port_host)
        elif self.proto == 'TCP Server':
            host = self.comboBox_host.currentText()
            match_client = True  # 只发送给一个客户端
            if host == u'所有连接':
                match_client = False
            else:
                ip_host, port_host = host.split(':')
                port_host = int(port_host)
            for client in self.client_list:
                if match_client and client.peerAddress().toString(
                ) == ip_host and client.peerPort() == port_host:
                    # 找到对应的client
                    client.write(b)
                elif not match_client:
                    client.write(b)
        else:
            self.net.send(b)

    def slot_send(self):
        '''发送按钮按下事件'''
        if self.net:
            text = self.textEdit_send.toPlainText()
            if text:
                try:
                    if self.hex_send:
                        text = text.replace(' ', '')  # 删除无效的空格
                        if len(text) % 2 != 0:
                            #十六进制发送输入的长度必须是2的倍数
                            raise Exception('十六进制输入的长度必须是2的倍数')
                        b = a2b_hex(text)
                    else:
                        b = bytes(text, encoding='utf-8')
                    self.__send(b)

                except Exception as e:
                    QMessageBox.critical(self, '错误', '%s' % e)
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
        if self.textBrowser.toPlainText():
            self.textBrowser.clear()

    def slot_save_view(self):
        '''保存显示'''
        if not self.textBrowser.toPlainText():
            # 没有数据直接退出
            return

        file_name, state = QFileDialog.getSaveFileName(self, '保存文件', './',
                                                       'Text文件(*.txt)')
        if state:
            with open(file_name, 'w') as f:
                f.write(self.textBrowser.toPlainText())
            QMessageBox.information(self, '成功', '%s文件保存成功! ' % file_name)

    def tcpServer_onConnection(self):
        '''TCP Server有客户端连接进来'''
        client = self.net.sock.nextPendingConnection()
        client.readyRead.connect(self.tcpServer_dataRecvie)
        # 客户端退出绑定clientExit
        client.disconnected.connect(self.tcpServer_clientExit)
        client.error.connect(self.tcpServer_clientExit)

        self.client_list.append(client)

        ip = client.peerAddress().toString()
        port = client.peerPort()
        client_info = '%s:%s' % (ip, port)
        self.comboBox_host.addItem(client_info)

    def tcpServer_clientExit(self):
        '''TCP Server下客户端退出（正常断开/异常退出）'''
        client = self.sender()
        try:
            client.close()
            self.client_list.remove(client)
        except:
            pass

        ip = client.peerAddress().toString()
        port = client.peerPort()
        client_info = '%s:%s' % (ip, port)
        self._comboBox_removeItem_byName(self.comboBox_host, client_info)

    def _comboBox_removeItem_byName(self, combo, name):
        '''QComboBox中删除特定名字的项目'''
        for i in range(0, combo.count()):
            if name == combo.itemText(i):
                # 找到对应的项目
                combo.removeItem(i)

    def tcpServer_dataRecvie(self):
        '''TCP Server数据处理'''
        if self.net:
            for client in self.client_list:
                if client.bytesAvailable() > 0:
                    ip = client.peerAddress().toString()
                    port = client.peerPort()
                    client_info = '[From %s:%s] ' % (ip, port)

                    data = client.readAll()

                    self.__view(data, prefix=client_info)

    def slot_hex_send_change(self, state):
        '''十六进制发送'''
        self.hex_send = True if state else False

    def slot_host_clear(self):
        '''清除主机/断开客户端'''

        if self.client_list:
            #断开客户端
            clients = self.client_list.copy()
            host = self.comboBox_host.currentText()
            ip, port = host.split(':')
            for c in clients:
                if c.peerAddress().toString() == ip and int(
                        port) == c.peerPort:
                    c.close()
        else:
            self.comboBox_host.clearEditText()
            self.comboBox_host.clear()

    def slot_input_clear(self):
        '''清除输入'''
        if self.textEdit_send.toPlainText():
            self.textEdit_send.clear()

    def slot_input_from_file(self):
        '''文件发送'''

        # self.file_send=True

        file_name, state = QFileDialog.getOpenFileName(self, u'打开文件', './',
                                                       u'所有文件(*.*)')
        if state:
            with open(file_name, 'rb') as f:
                b = f.read()
                self.__send(b)

    def slot_save_view_file_change(self, state):
        '''接收转向文件'''
        self.save_file = True if state else False
        if state:
            file_name, ok = QFileDialog.getSaveFileName(
                self, u'保存文件', './', u'所有文件(*.*)')
            if ok:
                self.save_file_name = file_name
        else:
            self.save_file_name = None


class NetHelper(object):
    '''TCP/UDP 统一接口类'''

    sock = None  # 记录当前连接的sock
    sock_type = None  # 记录当前连接的sock类型

    # ip = None # 记录当前连接的IP地址
    port = None  # 记录当前连接的端口号

    def __init__(self, **kwargs):
        self.open(**kwargs)

    def open(self, sock_type='TCP Client', ip='127.0.0.1', port=2007):
        '''打开网络设备，建立连接
        @sock_type:
            'TCP Client','TCP Server','UDP'
        '''
        self.sock_type = sock_type
        # self.ip = ip
        self.port = port

        if sock_type == 'TCP Client':
            tcp_client = QTcpSocket()
            tcp_client.connectToHost(ip, port)
            self.sock = tcp_client
        elif sock_type == 'TCP Server':
            tcp_server = QTcpServer()
            tcp_server.listen(QHostAddress(ip), port)
            self.sock = tcp_server

        elif sock_type == 'UDP':
            udp = QUdpSocket()
            udp.bind(QHostAddress(ip), port)
            self.sock = udp
        else:
            print('Unkonw sock_type=%r' % sock_type)

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
        '''读取所有数据
        @return:
            tuple(data,[from])
        '''
        if self.sock_type == 'TCP Client':
            data = self.sock.readAll()
            return (data, None)
        elif self.sock_type == 'TCP Server':
            pass
        elif self.sock_type == 'UDP':
            data, host, port = self.sock.readDatagram(self.port)
            data = QtCore.QByteArray(data)
            return (data, [host, port])
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
            pass
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
