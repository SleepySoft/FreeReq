import os
from typing import List, Dict
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QStandardItemModel, QDesktopServices
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableView, \
    QFileDialog, QAbstractItemView, QDockWidget, QHeaderView, QMessageBox

from FreeReq import IReqAgent, RequirementUI, STATIC_META_ID_PREFIX, STATIC_FIELD_ID
from plugin.TestcaseIndexer.TestcaseFileNameScanner import TestcaseFileNameScanner
from plugin.TestcaseIndexer.TestcaseScannerBase import TestcaseScannerBase


# ----------------------------------------------------------------------------------------------------------------------

req_agent: IReqAgent = None


# ----------------------------------------------------------------------------------------------------------------------

class TestcaseSelector(QWidget):
    def __init__(self, main_ui: 'RequirementUI', scanner: TestcaseScannerBase):
        super().__init__()
        self.main_ui = main_ui
        self.scanner = scanner
        self.patterns = []
        self.filter = ''
        self.table_view = QTableView()
        self.scan_path = ''         # TODO: Load from config
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

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

        # Path input and buttons
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.scan_path)
        self.path_input.setPlaceholderText("Scan path")
        path_layout.addWidget(self.path_input)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_path)
        path_layout.addWidget(self.browse_button)

        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.on_button_scan_files)
        path_layout.addWidget(self.scan_button)

        layout.addLayout(path_layout)

    def set_req_id_filter(self, req_filter: str):
        self.filter = req_filter
        self.update_testcase_index()

    def set_scan_path(self, scan_path: str):
        self.scan_path = scan_path
        self.path_input.setText(self.scan_path)

    def set_scan_pattern(self, patterns: List[str]):
        self.patterns = patterns

    def browse_path(self):
        # Browse and set the scan path
        path = QFileDialog.getExistingDirectory(self, "Select Scan Path")
        if path:
            self.scan_path = path
            self.path_input.setText(path)
            if hasattr(self.main_ui, 'set_scan_path'):
                self.main_ui.set_scan_path(path)

    def on_button_scan_files(self):
        self.scan_files()
        QMessageBox.information(self, 'Scan Finished',
                                f'Scan Finished. Total test case: {self.scanner.testcase_count()}')

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

        files = mapping.get(self.filter, [])
        for file_path in files:
            file_name = os.path.basename(file_path)
            row = self.table_model.rowCount()
            self.table_model.insertRow(row)
            self.table_model.setData(self.table_model.index(row, 0), file_name)
            self.table_model.setData(self.table_model.index(row, 1), file_path)

        # 自动调整列宽度
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def open_file(self, index):
        file_path = self.table_model.data(self.table_model.index(index.row(), 1))
        if file_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))


test_case_viewer: TestcaseSelector = None
dock_test_case_viewer: QDockWidget = None


def on_hook_req_loaded(_):
    meta_config = req_agent.get_req_meta()

    req_id_prefix = meta_config.get(STATIC_META_ID_PREFIX)
    req_id_pattern = [prefix + r'\d{5}' for prefix in req_id_prefix]
    test_case_viewer.set_scan_pattern(req_id_pattern)

    guess_test_case_path = os.path.join(req_agent.get_req_path(), 'Testcase')
    if os.path.exists(guess_test_case_path):
        test_case_viewer.set_scan_path(guess_test_case_path)

    test_case_viewer.scan_files()


def on_hook_requirement_tree_selection_changed(_, __):
    _, req_node = test_case_viewer.main_ui.get_selected()
    if req_node is not None:
        test_case_viewer.set_req_id_filter(req_node.get(STATIC_FIELD_ID, ''))


def on_test_case_selector_button_click():
    if dock_test_case_viewer.isVisible():
        dock_test_case_viewer.hide()
    else:
        dock_test_case_viewer.show()
    # test_case_viewer.show_right_upper()


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
    global test_case_viewer
    global dock_test_case_viewer

    dock_test_case_viewer = QDockWidget("Testcase Link", req_ui)
    test_case_viewer = TestcaseSelector(req_ui, TestcaseFileNameScanner('', []))

    dock_test_case_viewer.hide()
    dock_test_case_viewer.setWidget(test_case_viewer)
    req_ui.addDockWidget(Qt.RightDockWidgetArea, dock_test_case_viewer)

    req_ui.on_req_loaded.add_post_hook(on_hook_req_loaded)
    req_ui.on_requirement_tree_selection_changed.add_post_hook(on_hook_requirement_tree_selection_changed)

    test_case_selector_button = QPushButton('Testcase Link')
    test_case_selector_button.clicked.connect(on_test_case_selector_button_click)
    req_ui.edit_board.layout_plugin_area.addWidget(test_case_selector_button)
