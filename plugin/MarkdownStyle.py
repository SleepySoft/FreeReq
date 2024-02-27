import os
import glob
from typing import List, Dict

from PyQt5.QtWidgets import QComboBox
from FreeReq import IReqAgent, RequirementUI


# ----------------------------------------------------------------------------------------------------------------------

main_ui: RequirementUI = None
req_agent: IReqAgent = None


# ----------------------------------------------------------------------------------------------------------------------

class CssSelector(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(False)
        self.setMinimumWidth(180)
        self.currentIndexChanged.connect(self.on_style_selector_changed)

    def showPopup(self):
        super().showPopup()
        self.scan_style_files()

    def scan_style_files(self):
        # 扫描MarkdownStyle文件夹下的所有css文件
        try:
            css_files = glob.glob(os.path.join(os.path.dirname(__file__), 'MarkdownStyle', '*.css'))
            # 清空combobox
            self.clear()
            # 将css文件名添加到combobox
            for css_file in css_files:
                self.addItem(os.path.basename(css_file))
        except FileNotFoundError:
            print("MarkdownStyle folder dose not exist.")

    def on_style_selector_changed(self):
        selected_file = self.currentText()
        if selected_file == '':
            return
        # 响应选择变化的事件
        try:
            file_abs_path = os.path.join(os.path.dirname(__file__), 'MarkdownStyle', selected_file)
            with open(file_abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
                main_ui.module.MARK_DOWN_CSS_TABLE = content
                main_ui.edit_board.render_markdown()
        except FileNotFoundError:
            print("Open CSS file fail.")
        except Exception as e:
            print(e)
        finally:
            pass


# ----------------------------------------------------------------------------------------------------------------------


def plugin_prob() -> Dict[str, str]:
    return {
        'name': 'MarkdownStyle',
        'version': '1.0.0.0',
        'tags': 'style, css'
    }


def plugin_capacities() -> List[str]:
    return []


# ----------------------------------------------------------------------------------------------------------------------

css_selector: CssSelector = None


def req_agent_prepared(req: IReqAgent):
    global req_agent
    req_agent = req


def after_ui_created(req_ui: RequirementUI):
    global main_ui, css_selector
    main_ui = req_ui

    css_selector = CssSelector()
    main_ui.edit_board.layout_plugin_area.addWidget(css_selector)
