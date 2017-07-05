#coding: utf-8
'''网络调试助手（PyQt版本）
@初衷：
    设计跨平台使用的网络调试助手
@参考原型：
    参考Windows版本的网络调试助手（NetAssist野人版）
'''
from netassistant import NetAssistant
from PyQt5.QtWidgets import QApplication
import sys


def main():
    app = QApplication(sys.argv)
    win = NetAssistant()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()