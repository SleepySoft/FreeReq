import os
from typing import Dict, List, Tuple

from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout, QWidget
from FreeReq import IReqAgent, RequirementUI


self_path = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------------------------------------------------

main_ui: RequirementUI = None
req_agent: IReqAgent = None


# ----------------------------------------------------------------------------------------------------------------------
class ScratchPaper(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.textEdit = QTextEdit(self)
        self.settings = QSettings("SleepySoft", "FreeReq")
        self.text_changed = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Scratch Paper')
        # self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.setWindowFlags(
            Qt.Window |  # 标准窗口框架
            Qt.WindowTitleHint |  # 添加窗口标题栏
            Qt.WindowSystemMenuHint |  # 添加系统菜单（在标题栏上右键时出现）
            Qt.WindowMinMaxButtonsHint |  # 添加最大化和最小化按钮
            Qt.WindowCloseButtonHint  # 添加关闭按钮
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.textEdit)

        font = QFont()
        font.setPointSize(12)
        self.textEdit.setFont(font)

        # Load the file content when initializing
        try:
            with open(self.__scratch_paper_path(), 'r', encoding='utf-8') as f:
                self.textEdit.setPlainText(f.read())
        except Exception as e:
            print(e)

        # Set up a timer to save the file every 2 seconds
        self.timer.timeout.connect(self.auto_save)
        self.timer.start(2000)  # time in milliseconds

    def on_text_changed(self):
        self.text_changed = True

    def auto_save(self):
        if self.text_changed:
            with open(self.__scratch_paper_path(), 'w', encoding='utf-8') as f:
                f.write(self.textEdit.toPlainText())
            self.text_changed = False

    def closeEvent(self, event):
        # Save the window size
        self.settings.setValue("windowSize", self.size())
        event.ignore()
        self.hide()

    def showEvent(self, event):
        # Restore the window size
        if self.settings.contains("windowSize"):
            self.resize(self.settings.value("windowSize"))

    def __scratch_paper_path(self):
        return os.path.join(self_path, 'scratch.txt')


# ----------------------------------------------------------------------------------------------------------------------

scratch_paper: ScratchPaper = None


def on_template_button_click():
    global scratch_paper
    if scratch_paper is None:
        scratch_paper = ScratchPaper(main_ui)
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
