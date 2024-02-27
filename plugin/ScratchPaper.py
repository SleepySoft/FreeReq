import sys
from typing import Dict, List, Tuple

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton, QApplication, QMainWindow, QTextEdit
from FreeReq import IReqAgent, RequirementUI


# ----------------------------------------------------------------------------------------------------------------------

main_ui: RequirementUI = None
req_agent: IReqAgent = None


# ----------------------------------------------------------------------------------------------------------------------

class ScratchPaper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.textEdit = QTextEdit(self)
        self.text_changed = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Scratch Paper')

        self.setCentralWidget(self.textEdit)
        self.textEdit.textChanged.connect(self.on_text_changed)

        font = QFont()
        font.setPointSize(12)
        self.textEdit.setFont(font)

        # Load the file content when initializing
        try:
            with open('scratch.txt', 'r') as f:
                self.textEdit.setText(f.read())
        except Exception as e:
            print(e)
        finally:
            pass

        # Set up a timer to save the file every 2 seconds
        self.timer.timeout.connect(self.auto_save)
        self.timer.start(2000)  # time in milliseconds

    def on_text_changed(self):
        self.text_changed = True

    def auto_save(self):
        if self.text_changed:
            with open('scratch.txt', 'w') as f:
                f.write(self.textEdit.toPlainText())
            self.text_changed = False

    def closeEvent(self, event):
        # Override the closeEvent method to hide the window instead of closing it
        event.ignore()
        self.hide()


# ----------------------------------------------------------------------------------------------------------------------

scratch_paper: ScratchPaper = None


def on_template_button_click():
    global scratch_paper
    if scratch_paper is None:
        scratch_paper = ScratchPaper()
    scratch_paper.show()


# ----------------------------------------------------------------------------------------------------------------------


def plugin_prob() -> Dict[str, str]:
    return {
        'name': 'ScratchPaper',
        'version': '1.0.0.0',
        'tags': 'scratch'
    }


def plugin_capacities() -> List[str]:
    return []


# ----------------------------------------------------------------------------------------------------------------------

def req_agent_prepared(req: IReqAgent):
    global req_agent
    req_agent = req


def after_ui_created(req_ui: RequirementUI):
    global main_ui
    main_ui = req_ui
    template_button = QPushButton('ScratchPaper')
    main_ui.edit_board.layout_plugin_area.addWidget(template_button)
    template_button.clicked.connect(on_template_button_click)
