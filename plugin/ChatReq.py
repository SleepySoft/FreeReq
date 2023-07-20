from typing import Union, List, Dict
from FreeReq import IReqObserver, ReqNode, RequirementUI, IReqAgent

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal

from FreeReq import plugin_manager
from plugin.EmbeddingIndexing import EmbeddingIndexing


# ----------------------------------------------------------------------------------------------------------------------

EMBEDDING_PLUGIN_NAME = 'EmbeddingIndexing'


# ----------------------------------------------------------------------------------------------------------------------

class ChatWindow(QWidget):
    send_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.__init_ui()
        self.thread = WorkerThread()
        self.send_message.connect(self.thread.handle_input)
        self.thread.append_text.connect(self.append_text)
        self.thread.start()

    def __init_ui(self):
        vbox = QVBoxLayout()
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        vbox.addWidget(self.text_display, 8)

        hbox = QHBoxLayout()
        self.text_input = QLineEdit()
        hbox.addWidget(self.text_input, 4)
        send_button = QPushButton('发送')
        send_button.clicked.connect(self.send)
        hbox.addWidget(send_button, 1)

        vbox.addLayout(hbox, 2)
        self.setLayout(vbox)

        self.setWindowTitle('Chat')
        self.resize(800, 600)

    def send(self):
        text = self.text_input.text()
        if text:
            self.send_message.emit(text)
            self.text_input.clear()

    def append_text(self, text):
        self.text_display.append(text)

    def closeEvent(self, event):
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)


class WorkerThread(QThread):
    append_text = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def handle_input(self, text: str):
        text = text.strip()
        if text != '':
            self.append_text.emit(text)
            search_result = plugin_manager.call_module_function(EMBEDDING_PLUGIN_NAME, 'search_req_nodes', text)


# ----------------------------------------------------------------------------------------------------------------------

chat_window: ChatWindow = None


def on_chat():
    global chat_window
    if chat_window is None:
        chat_window = ChatWindow()
    chat_window.show()


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> Dict[str, str]:
    return {
        'name': 'ChatRequirement',
        'version': '1.0.0.0',
        'tags': 'llm'
    }


def plugin_capacities() -> List[str]:
    return []


# ----------------------------------------------------------------------------------------------------------------------

def req_agent_prepared(req: IReqAgent):
    pass


def after_ui_created(req_ui: RequirementUI):
    global main_ui
    main_ui = req_ui
    chat_button = QPushButton('Chat')
    main_ui.edit_board.layout_plugin_area.addWidget(chat_button)
    chat_button.clicked.connect(on_chat)


# ----------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_window = ChatWindow()
    chat_window.show()
    sys.exit(app.exec_())

