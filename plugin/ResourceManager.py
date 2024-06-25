import os
import re
from typing import List, Dict

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QPushButton, QTableWidget, QWidget, QVBoxLayout, QMessageBox, QTableWidgetItem, \
    QHBoxLayout
from FreeReq import IReqAgent, RequirementUI, ReqNode, STATIC_FIELD_CONTENT

# ----------------------------------------------------------------------------------------------------------------------

main_ui: RequirementUI = None
req_agent: IReqAgent = None


# ----------------------------------------------------------------------------------------------------------------------


def normalize_path_splitter(path: str) -> str:
    return path.replace('\\', '/')


def find_resources_in_markdown(markdown_text):
    # Markdown链接的正则表达式
    pattern = r'\[.*?\]\((.*?)\)'
    # 使用正则表达式找到所有的链接
    resources = re.findall(pattern, markdown_text)
    return resources


class ResourceManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.table_widget = QTableWidget()
        self.scan_button = QPushButton('Scan')
        self.auto_clear_button = QPushButton('Auto Clear')
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Resource Manager')
        self.setMinimumSize(1024, 768)

        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(['Req UUID', 'Resource', 'Status'])

        self.scan_button.clicked.connect(self.refresh_resource_table)
        self.auto_clear_button.clicked.connect(self.auto_clear)

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)

        line = QHBoxLayout()
        line.addWidget(self.scan_button)
        line.addWidget(self.auto_clear_button)
        layout.addLayout(line)

        main_widget = QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def refresh_resource_table(self):
        req_resource = self.search_req_resource()
        attachment_resource = self.search_attachment_file()

        self.table_widget.setRowCount(0)

        for uuid, resources in req_resource.items():
            for resource in resources:
                row_position = self.table_widget.rowCount()
                self.table_widget.insertRow(row_position)

                self.table_widget.setItem(row_position, 0, QTableWidgetItem(uuid))
                self.table_widget.setItem(row_position, 1, QTableWidgetItem(resource))

                if normalize_path_splitter(resource) in attachment_resource:
                    self.table_widget.setItem(row_position, 2, QTableWidgetItem('OK'))
                else:
                    self.table_widget.setItem(row_position, 2, QTableWidgetItem('Invalid'))

        req_resource_norm = [normalize_path_splitter(value) for values in req_resource.values() for value in values]
        for resource in attachment_resource:
            if resource not in req_resource_norm:
                row_position = self.table_widget.rowCount()
                self.table_widget.insertRow(row_position)

                self.table_widget.setItem(row_position, 1, QTableWidgetItem(resource))
                self.table_widget.setItem(row_position, 2, QTableWidgetItem('No Reference'))
        self.table_widget.resizeColumnsToContents()

    def auto_clear(self):
        unused_files = [resource for resource in self.search_attachment_file()
                        if resource not in [value for values in self.search_req_resource().values() for value in values]]

        if unused_files:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setText("This operation will delete all unreferenced resource files. Are you sure?")
            msg.setInformativeText("\n".join(unused_files))
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            retval = msg.exec_()

            if retval == QMessageBox.Ok:
                for file in unused_files:
                    os.remove(file)

                self.refresh_resource_table()

    def search_req_resource(self) -> dict:
        def resource_collector(node: ReqNode, context: dict):
            content = node.get(STATIC_FIELD_CONTENT)
            if content is not None:
                resources = find_resources_in_markdown(content)
                if len(resources) > 0:
                    context[node.get_uuid()] = resources
        resource_table = req_agent.req_map(req_agent.get_req_root(), resource_collector)
        return resource_table

    def search_attachment_file(self):
        # Ugly directly access
        search_folder = main_ui.edit_board.text_md_editor.attachment_folder
        all_items = os.listdir(search_folder)
        rel_items = [normalize_path_splitter(os.path.join(search_folder, item)) for item in all_items]
        files = [item for item in rel_items if os.path.isfile(item)]
        return files


# ----------------------------------------------------------------------------------------------------------------------


def plugin_prob() -> Dict[str, str]:
    return {
        'name': 'ResourceManager',
        'version': '1.0.0.0',
        'tags': 'resource'
    }


def plugin_capacities() -> List[str]:
    return []


# ----------------------------------------------------------------------------------------------------------------------

resource_manager: ResourceManager = None


def on_resource_manager_button_click():
    if resource_manager is not None:
        resource_manager.show()


def req_agent_prepared(req: IReqAgent):
    global req_agent
    req_agent = req


def after_ui_created(req_ui: RequirementUI):
    global main_ui, resource_manager
    main_ui = req_ui

    resource_manager = ResourceManager()
    resource_manager_button = QPushButton('Resource Manager')
    resource_manager_button.clicked.connect(on_resource_manager_button_click)
    main_ui.edit_board.layout_plugin_area.addWidget(resource_manager_button)
