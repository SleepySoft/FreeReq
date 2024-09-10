import os
import glob
from typing import List, Dict

from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QComboBox, QFileDialog, QAbstractItemView
from FreeReq import IReqAgent, RequirementUI, STATIC_META_ID_PREFIX, ReqNode, IReqObserver
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QDesktopServices
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableView, QMessageBox


# ----------------------------------------------------------------------------------------------------------------------
from plugin.TestcaseIndexer.TestcaseFileNameScanner import TestcaseFileNameScanner
from plugin.TestcaseIndexer.TestcaseScannerBase import TestcaseScannerBase
from extra.MonkeyHook import MonkeyHook

req_agent: IReqAgent = None


# ----------------------------------------------------------------------------------------------------------------------

class TestcaseSelector(QWidget):
    def __init__(self, main_ui: 'RequirementUI', scanner: TestcaseScannerBase):
        super().__init__()
        self.main_ui = main_ui
        self.scanner = scanner
        self.patterns = []
        self.table_view = QTableView()
        self.scan_path = self.main_ui.get_scan_path() if hasattr(self.main_ui, 'get_scan_path') else ''
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Testcase Selector")
        layout = QVBoxLayout(self)

        # Path input and buttons
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.scan_path)
        self.path_input.setPlaceholderText("Scan path")
        path_layout.addWidget(self.path_input)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_path)
        path_layout.addWidget(self.browse_button)

        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.scan_files)
        path_layout.addWidget(self.scan_button)

        layout.addLayout(path_layout)

        # 初始化表格视图和模型
        self.table_model = QStandardItemModel()

        # 设置模型
        self.table_view.setModel(self.table_model)

        # 设置选择模式为单行选择
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)

        # 设置选择行为为选择整行
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)

        # 禁止编辑
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # 连接双击事件到打开文件的槽函数
        self.table_view.doubleClicked.connect(self.open_file)

        # 将表格视图添加到布局中
        layout.addWidget(self.table_view)

        # Load the scan path
        self.load_scan_path()

    def load_scan_path(self):
        # Load the scan path from the main UI or a config file
        self.path_input.setText(self.scan_path)

    def update_scan_pattern(self, patterns: List[str]):
        self.patterns = patterns

    def browse_path(self):
        # Browse and set the scan path
        path = QFileDialog.getExistingDirectory(self, "Select Scan Path")
        if path:
            self.scan_path = path
            self.path_input.setText(path)
            if hasattr(self.main_ui, 'set_scan_path'):
                self.main_ui.set_scan_path(path)

    def scan_files(self):
        # Perform the scan and update the table
        self.scanner.scan_path = self.scan_path
        self.scanner.scan_patterns = self.patterns
        self.scanner.do_scan()
        self.update_testcase_index()

    def update_testcase_index(self):
        # Update the table view with the new mapping
        mapping = self.scanner.get_mapping()
        self.table_model.clear()
        self.table_model.setRowCount(0)
        self.table_model.setHorizontalHeaderLabels(["File Name", "Path"])
        for req_id, files in mapping.items():
            for file_path in files:
                file_name = os.path.basename(file_path)
                row = self.table_model.rowCount()
                self.table_model.insertRow(row)
                self.table_model.setData(self.table_model.index(row, 0), file_name)
                self.table_model.setData(self.table_model.index(row, 1), file_path)

    def open_file(self, index):
        if index.column() == 0:
            file_path = self.table_model.data(self.table_model.index(index.row(), 1))
            if file_path:
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def closeEvent(self, event):
        # Hide the window instead of closing it
        self.hide()
        event.ignore()


test_case_selector: TestcaseSelector = None


def on_test_case_selector_button_click():
    test_case_selector.show()


class TestcaseLinkObserver(IReqObserver):
    def __init__(self):
        super(TestcaseLinkObserver, self).__init__()

    def on_req_saved(self, req_uri: str):
        pass

    def on_req_loaded(self, req_uri: str):
        meta_config = req_agent.get_req_meta()
        req_id_prefix = meta_config.get(STATIC_META_ID_PREFIX)
        req_id_pattern = [prefix + r'\d{5}' for prefix in req_id_prefix]
        test_case_selector.update_scan_pattern(req_id_pattern)
        test_case_selector.scan_files()

    def on_req_closed(self, req_uri: str):
        pass

    def on_req_exception(self, exception_name: str, **kwargs):
        pass

    def on_meta_data_changed(self, req_name: str):
        pass

    def on_node_data_changed(self, req_name: str, req_node: ReqNode):
        pass

    def on_node_structure_changed(self, req_name: str, parent_node: ReqNode, child_node: [ReqNode], operation: str):
        pass


def on_hook_requirement_tree_selection_changed(self, selected, deselected):
    pass


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> Dict[str, str]:
    return {
        'name': 'TestcaseLink',
        'version': '1.0.0.0',
        'tags': 'testcase, test'
    }


def plugin_capacities() -> List[str]:
    return []


# ----------------------------------------------------------------------------------------------------------------------


def req_agent_prepared(req: IReqAgent):
    global req_agent
    req_agent = req


def after_ui_created(req_ui: RequirementUI):
    global test_case_selector
    test_case_selector = TestcaseSelector(req_ui, TestcaseFileNameScanner('', []))
    req_agent.add_observer(TestcaseLinkObserver())

    req_ui.on_requirement_tree_selection_changed = \
        MonkeyHook(req_ui.on_requirement_tree_selection_changed,
                   hook_after=on_hook_requirement_tree_selection_changed)

    test_case_selector_button = QPushButton('Testcase Link')
    test_case_selector_button.clicked.connect(on_test_case_selector_button_click)
    req_ui.edit_board.layout_plugin_area.addWidget(test_case_selector_button)




