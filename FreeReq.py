from __future__ import annotations

import json
import os
import sys
import uuid
import traceback

try:
    # Use try catch for running FreeReq without UI

    from PyQt5 import QtCore
    from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem, QCursor
    from PyQt5.QtCore import pyqtSignal, Qt, QAbstractTableModel, QModelIndex, QRect, QVariant, QSize, QTimer, \
        QAbstractItemModel, QPoint
    from PyQt5.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QGridLayout, QWidget, QPushButton, \
        QDockWidget, QAction, qApp, QMessageBox, QDialog, QVBoxLayout, QLabel, QGroupBox, QTableWidget, \
        QTableWidgetItem, QTabWidget, QLayout, QTextEdit, QListWidget, QListWidgetItem, QMenu, QHeaderView, \
        QStyle, QStyleOptionButton, QTableView, QLineEdit, QCheckBox, QFileDialog, QComboBox, QTreeView, \
        QAbstractItemView, QInputDialog
except Exception as e:
    print('UI disabled.')
    print(str(e))
    print(traceback.format_exc())
finally:
    pass

self_path = os.path.dirname(os.path.abspath(__file__))


CONST_FIELD_ID = 'id'
CONST_FIELD_UUID = 'uuid'
CONST_FIELD_TITLE = 'title'
CONST_FIELD_CHILD = 'child'

CONST_FIELDS = [CONST_FIELD_ID, CONST_FIELD_UUID, CONST_FIELD_TITLE, CONST_FIELD_CHILD]


class ReqNode:
    def __call__(self):
        return self

    def __init__(self, title: str = ''):
        self.__data = {
            CONST_FIELD_ID: '',
            CONST_FIELD_UUID: str(uuid.uuid4().hex),
            CONST_FIELD_TITLE: title,
            CONST_FIELD_CHILD: [],
        }
        self.__parent = None
        self.__sibling = self.__parent.children() if self.__parent is not None else []
        self.__children = []

    # -------------------------------------- Data ---------------------------------------

    def get(self, key: str) -> any:
        return self.__data.get(key, None)

    def set(self, key: str, val: any):
        if key != CONST_FIELD_CHILD:
            self.__data[key] = val
        else:
            raise ValueError('The key cannot be "%s"' % CONST_FIELD_CHILD)

    def data(self) -> dict:
        return self.__data

    def get_uuid(self) -> str:
        return self.__data.get(CONST_FIELD_UUID, '')

    def set_title(self, text: str):
        self.__data[CONST_FIELD_TITLE] = text

    def get_title(self) -> str:
        return self.__data.get(CONST_FIELD_TITLE, 'N/A')

    # ------------------------------------ Property ------------------------------------

    def order(self) -> int:
        return self.__sibling.index(self)

    def child_count(self) -> int:
        return len(self.__children)

    # ------------------------------------ Iteration ------------------------------------

    def parent(self) -> ReqNode:
        return self.__parent

    def sibling(self) -> [ReqNode]:
        return self.__sibling

    def prev(self) -> ReqNode:
        order = self.order()
        return self.__sibling[order - 1] if order > 0 else None

    def next(self) -> ReqNode:
        order = self.order()
        return self.__sibling[order + 1] if order < len(self.__sibling) else None

    def child(self, order: int):
        return self.__children[order] if 0 <= order < len(self.__children) else None

    def children(self):
        return self.__children

    # ---------------------------------- Construction ----------------------------------

    def set_parent(self, parent: ReqNode):
        self.__parent = parent
        self.__sibling = self.__parent.children() if self.__parent is not None else []

    def append_child(self, node: ReqNode) -> int:
        node.set_parent(self)
        self.__children.append(node)
        return len(self.__children) - 1

    def remove_child(self, node: ReqNode) -> bool:
        if node in self.__children:
            self.__children.remove(node)
            return True
        else:
            return False

    def remove_children(self):
        self.__children.clear()

    def insert_sibling_left(self, node: ReqNode) -> int:
        node.set_parent(self)
        index = self.order()
        self.__sibling.insert(self.order(), node)
        return index

    def insert_sibling_right(self, node: ReqNode) -> int:
        node.set_parent(self)
        index = self.order() + 1
        self.__sibling.insert(self.order() + 1, node)
        return index

    # ------------------------------------ Persists ------------------------------------

    def to_dict(self) -> dict:
        dic = self.__data.copy()
        dic[CONST_FIELD_CHILD] = [c.to_dict() for c in self.__children]
        return dic

    def from_dict(self, dic: dict):
        self.__data = dic
        self.__children = []
        if CONST_FIELD_CHILD in dic.keys():
            for sub_dict in dic[CONST_FIELD_CHILD]:
                node = ReqNode()
                node.from_dict(sub_dict)
                self.append_child(node)
            del self.__data[CONST_FIELD_CHILD]


class IReqObserver:
    def __init__(self):
        pass

    def on_meta_data_changed(self, req_name: str):
        pass

    def on_node_data_changed(self, req_name: str, req_node: ReqNode):
        pass

    def on_node_child_changed(self, req_name: str, req_node: ReqNode):
        pass


class IReqAgent:
    def __init__(self):
        self.__observer: IReqObserver = None

    def init(self, *args, **kwargs) -> bool:
        pass

    # ----------------------- Req management -----------------------

    def list_req(self) -> [str]:
        pass

    def new_req(self, req_name: str) -> bool:
        pass

    def open_req(self, req_name: str) -> bool:
        pass

    def delete_req(self, req_name: str) -> bool:
        pass

    # --------------------- After select_op_req() ---------------------

    def get_req_name(self) -> str:
        pass

    def get_req_meta(self) -> dict:
        pass

    def set_req_meta(self, req_meta: dict) -> bool:
        pass

    def get_req_root(self) -> ReqNode:
        pass

    def get_req_node(self, req_uuid: str) -> ReqNode:
        pass

    # --------------------- Notification from remote ---------------------

    def inform_node_data_updated(self, req_node: ReqNode):
        pass

    def inform_node_child_updated(self, req_node: ReqNode):
        pass

    # ------------------------------ Observer ------------------------------

    def set_observer(self, ob: IReqObserver):
        self.__observer = ob

    def notify_meta_data_changed(self, req_name: str):
        self.__observer.on_meta_data_changed(req_name)

    def notify_node_data_changed(self, req_name: str, req_node: ReqNode):
        self.__observer.on_node_data_changed(req_name, req_node)

    def notify_node_child_changed(self, req_name: str, req_node: ReqNode):
        self.__observer.on_node_child_changed(req_name, req_node)


class ReqSingleJsonFileAgent(IReqAgent):
    def __init__(self, req_path: str = self_path):
        super(ReqSingleJsonFileAgent, self).__init__()
        self.__req_path = req_path
        self.__req_name = ''
        self.__req_file_name = ''
        self.__req_meta_dict = {}
        self.__req_data_dict = {}
        self.__req_node_index = {}
        self.__req_node_root: ReqNode = None

    def init(self) -> bool:
        return True

    # ----------------------- Req management -----------------------

    def list_req(self) -> [str]:
        req_names = []
        for f in os.scandir(self.__req_path):
            if f.is_file() and f.name.lower().endswith('.req'):
                req_names.append(f.name[:-4])
        return req_names

    def new_req(self, req_name: str, overwrite: bool = False) -> bool:
        if not overwrite and req_name in self.list_req():
            return False
        self.__req_name = req_name
        self.__req_file_name = req_name + '.req'
        self.__req_node_root = ReqNode(req_name)
        return True

    def open_req(self, req_name: str) -> bool:
        if req_name not in self.list_req():
            return False
        self.__req_name = req_name
        self.__req_file_name = req_name + '.req'
        return self.__load_req_json()

    def delete_req(self, req_name: str) -> bool:
        return False

    # --------------------- After select_op_req() ---------------------

    def get_req_name(self) -> str:
        return self.__req_name

    def get_req_meta(self) -> dict:
        return self.__req_meta_dict

    def set_req_meta(self, req_meta: dict) -> bool:
        self.__req_meta_dict = req_meta
        return self.save_req_json()

    def get_req_root(self) -> ReqNode:
        return self.__req_node_root

    def get_req_node(self, req_uuid: str) -> ReqNode:
        return self.__req_node_index.get(req_uuid, None)

    def req_map(self, map_operation) -> dict:
        """
        Iterate all nodes and call map_operation with each node
        :param map_operation: Callable object.
                            : Declaration: f(node: ReqNode, context: dict)
                            :   node: Current node in iteration.
                            :   context: A dict that pass to map_operation and finally return by req_map()
        :return: The context that passed to map_operation
        """
        context = {}
        self.__node_iteration(self.__req_node_root, map_operation, context)
        return context

    def __node_iteration(self, node: ReqNode, map_operation, context: dict):
        if node is not None:
            map_operation(node, context)
            for child_node in node.children():
                self.__node_iteration(child_node, map_operation, context)

    # --------------------- Notification from remote ---------------------

    def inform_node_data_updated(self, req_node: ReqNode):
        self.__save_req_json()

    def inform_node_child_updated(self, req_node: ReqNode):
        self.__save_req_json()

    # -------------------------------------------------------------------------------

    def __load_req_json(self) -> bool:
        try:
            with open(self.__req_file_name, 'rt') as f:
                json_dict = json.load(f)
                self.__req_meta_dict = json_dict.get('req_meta', {})
                self.__req_data_dict = json_dict.get('req_data', {})
                self.__req_dict_to_nodes()
                self.__build_node_index()
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())
            return False
        finally:
            pass
        return True

    def __save_req_json(self) -> bool:
        try:
            self.__build_node_index()
            self.__req_data_dict = self.__req_node_root.to_dict()
            json_dict = {
                'req_meta': self.__req_meta_dict,
                'req_data': self.__req_data_dict
            }

            with open(self.__req_file_name, 'wt') as f:
                json.dump(json_dict, f, indent=4)
        except Exception as e:
            print(str(e))
            print(traceback.format_exc())
            return False
        finally:
            pass
        return True

    def __req_dict_to_nodes(self):
        req_node_root = ReqNode()
        req_node_root.from_dict(self.__req_data_dict)
        self.__req_node_root = req_node_root

    def __build_node_index(self):
        req_node_index = self.req_map(lambda node, ctx: ctx.update({node.get_uuid(): node}))
        self.__req_node_index = req_node_index


class ReqModel(QAbstractItemModel):
    def __init__(self, req_data_agent: IReqAgent):
        super(ReqModel, self).__init__()

        self.__req_data_agent = req_data_agent

    # ------------------------------------- Method -------------------------------------

    def before_edit(self):
        self.layoutAboutToBeChanged.emit()

    def after_edit(self):
        self.layoutChanged.emit()

    # def set_root_node(self, root_node: ReqNode):
    #     self.__root_node = root_node
    #
    # def get_root_node(self) -> ReqNode:
    #     return self.__root_node

    @staticmethod
    def get_node_from_index(index: QModelIndex) -> ReqNode:
        return index.internalPointer() if index is not None and index.isValid() else None

    # ------------------------------------ Override ------------------------------------

    def data(self, index: QModelIndex, role=None):
        if index is None or not index.isValid():
            return None

        req_node: ReqNode = index.internalPointer()

        if role == Qt.DisplayRole:
            return req_node.get_title()

        return None

    # def flags(self, index: QModelIndex):
    #     if not index.isValid():
    #         return Qt.NoItemFlags
    #     return super().flags(index)

    # def headerData(self, p_int, orientation: Qt_Orientation, role=None):
    #     if orientation == Qt.Horizontal and role == Qt.DisplayRole:
    #         return self.__root_node.data().get(CONST_FIELD_TITLE, 'N/A')
    #     return None

    def index(self, row, column, parent: QModelIndex = None, *args, **kwargs):
        if self.__req_data_agent is None or self.__req_data_agent.get_req_root() is None:
            return QModelIndex()

        if parent is None or not parent.isValid():
            parent_item = self.__req_data_agent.get_req_root()
        else:
            parent_item: ReqNode = parent.internalPointer()

        if not QtCore.QAbstractItemModel.hasIndex(self, row, column, parent):
            return QModelIndex()

        child_item = parent_item.child(row)
        if child_item is not None:
            return QAbstractItemModel.createIndex(self, row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex = None):
        if self.__req_data_agent is None or self.__req_data_agent.get_req_root() is None:
            return QModelIndex()

        if index is None or not index.isValid():
            return QModelIndex()

        child_item: ReqNode = index.internalPointer()
        parent_item: ReqNode = child_item.parent()

        if parent_item is None:
            return QModelIndex()

        if parent_item == self.__req_data_agent.get_req_root():
            return QtCore.QAbstractItemModel.createIndex(self, 0, 0, parent_item)
        row = parent_item.order()

        return QtCore.QAbstractItemModel.createIndex(self, row, 0, parent_item)

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs):
        if self.__req_data_agent is None or self.__req_data_agent.get_req_root() is None:
            return 0

        if parent is None or not parent.isValid():
            parent_item = self.__req_data_agent.get_req_root()
        else:
            parent_item: ReqNode = parent.internalPointer()
        row_count = parent_item.child_count()

        return row_count

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs):
        # if parent.isValid():
        #     return len(parent.internalPointer().data())
        # return len(self.__root_node.data())
        return 1

    def headerData(self, section, orientation, role=0):
        if self.__req_data_agent is None:
            return None

        role = QtCore.Qt.ItemDataRole(role)
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            return self.__req_data_agent.get_req_name()
        return None


# From: https://doc.qt.io/qt-6/stylesheet-examples.html

TREE_VIEW_STYLE_SHEET = """

QTreeView {
    alternate-background-color: #f6fafb;
    background: #e8f4fc;
}
QTreeView::item:open {
    background-color: #c5ebfb;
    color: blue;
}
QTreeView::item:selected {
    background-color: #1d3dec;
    color: white;
}
QTreeView::branch {
    background-color: white;
}
QTreeView::branch:open {
    image: url(branch-open.png);
}
QTreeView::branch:closed:has-children {
    image: url(branch-closed.png);
}

QTreeView {
    show-decoration-selected: 1;
}

QTreeView::item {
    border: 1px solid #d9d9d9;
    border-top-color: transparent;
    border-bottom-color: transparent;
}

QTreeView::item:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
    border: 1px solid #bfcde4;
}

QTreeView::item:selected {
    border: 1px solid #567dbc;
}

QTreeView::item:selected:active{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);
}

QTreeView::item:selected:!active {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf);
}

QTreeView::branch {
        background: palette(base);
}

QTreeView::branch:has-siblings:!adjoins-item {
    border-image: url(res/vline.png) 0;
}

QTreeView::branch:has-siblings:adjoins-item {
    border-image: url(res/branch-more.png) 0;
}

QTreeView::branch:!has-children:!has-siblings:adjoins-item {
    border-image: url(res/branch-end.png) 0;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
        border-image: none;
        image: url(res/branch-closed.png);
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
        border-image: none;
        image: url(res/branch-open.png);
}
"""


class RequirementUI(QWidget):
    def __init__(self, req_data_agent: IReqAgent):
        super(RequirementUI, self).__init__()

        self.__req_data_agent = req_data_agent
        self.__req_model = ReqModel(self.__req_data_agent)

        self.__menu_on_node: ReqNode = None
        self.__menu_on_index: ReqNode = None

        self.__tree_requirements = QTreeView()
        self.__text_md_editor = QTextEdit()
        self.__text_md_preview = QTextEdit()
        self.__group_meta_data = QGroupBox()

        self.__init_ui()
        self.__update_req_display()

    def __init_ui(self):
        self.__layout_ui()
        self.__config_ui()

    def __layout_ui(self):
        root_layout = QHBoxLayout()
        self.setLayout(root_layout)

        root_layout.addWidget(self.__tree_requirements)

        right_area = QVBoxLayout()
        root_layout.addLayout(right_area)

        right_area.addWidget(self.__group_meta_data, 1)

        edit_area = QHBoxLayout()
        right_area.addLayout(edit_area, 9)

        edit_area.addWidget(self.__text_md_editor)
        edit_area.addWidget(self.__text_md_preview)

    def __config_ui(self):
        self.setMinimumSize(800, 600)
        self.setWindowTitle('Free Requirement - by Sleepy')

        self.__text_md_preview.setEnabled(False)
        # self.__tree_requirements.setModel(self.__req_model)
        # self.__tree_requirements.setRootIndex(self.__tree_requirements.rootIndex())
        self.__tree_requirements.setAlternatingRowColors(True)
        self.__tree_requirements.setStyleSheet(TREE_VIEW_STYLE_SHEET)
        self.__tree_requirements.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__tree_requirements.customContextMenuRequested.connect(self.on_requirement_tree_menu)

    def on_requirement_tree_menu(self, pos: QPoint):
        menu = QMenu()
        sel_index: QModelIndex = self.__tree_requirements.indexAt(pos)
        if sel_index is not None and sel_index.isValid():
            self.__menu_on_index = sel_index
            self.__menu_on_node = self.__req_model.get_node_from_index(sel_index)

            menu.addAction('Append Child', self.on_requirement_tree_menu_append_child)
            menu.addSeparator()
            menu.addAction('Insert sibling up', self.on_requirement_tree_menu_add_sibling_up)
            menu.addAction('Insert sibling down', self.on_requirement_tree_menu_add_sibling_down)
        else:
            self.__menu_on_node = None
            self.__menu_on_index = None

            menu.addAction('Add New Top Item', self.on_requirement_tree_menu_add_top_item)
            menu.addSeparator()
            menu.addAction('Create a New Requirement', self.on_requirement_tree_menu_create_new_req)
        menu.exec(QCursor.pos())

    def on_requirement_tree_menu_add_top_item(self):
        req_root = self.__req_data_agent.get_req_root()
        if req_root is not None:
            new_node = ReqNode('New Top Item')
            self.__req_model.before_edit()
            req_root.append_child(new_node)
            self.__req_model.after_edit()
            self.__req_data_agent.inform_node_data_updated(req_root)

    def on_requirement_tree_menu_append_child(self):
        if self.__menu_on_node is not None:
            new_node = ReqNode('New Item')
            self.__req_model.before_edit()
            self.__menu_on_node.append_child(new_node)
            self.__req_model.after_edit()
            self.__req_data_agent.inform_node_data_updated(self.__menu_on_node)

    def on_requirement_tree_menu_add_sibling_up(self):
        if self.__menu_on_node is not None:
            new_node = ReqNode('New Item')
            self.__req_model.before_edit()
            self.__menu_on_node.insert_sibling_left(new_node)
            self.__req_model.after_edit()
            self.__req_data_agent.inform_node_data_updated(self.__menu_on_node)

    def on_requirement_tree_menu_add_sibling_down(self):
        if self.__menu_on_node is not None:
            new_node = ReqNode('New Item')
            self.__req_model.before_edit()
            self.__menu_on_node.insert_sibling_right(new_node)
            self.__req_model.after_edit()
            self.__req_data_agent.inform_node_data_updated(self.__menu_on_node)

    def on_requirement_tree_menu_create_new_req(self):
        req_name, is_ok = QInputDialog.getText(
            self, "Create New Requirement", "Requirement Name: ", QLineEdit.Normal, "")
        req_name.strip()
        if is_ok and req_name != '':
            if req_name in self.__req_data_agent.list_req():
                ret = QMessageBox.question(
                    self, 'Overwrite', 'Requirement already exists.\n\nOverwrite?',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if ret != QMessageBox.Yes:
                    return
            if self.__req_data_agent.new_req(req_name):
                req_root = self.__req_data_agent.get_req_root()
                self.__req_model.before_edit()
                self.__root_node.append_child(req_root)
                self.__req_model.after_edit()

    def __update_req_display(self):
        self.__tree_requirements.setModel(self.__req_model)

        # req_name = self.__req_data_agent.get_req_name()
        # req_root = self.__req_data_agent.get_req_root()
        # if req_root is not None:
        #     self.__root_node = req_root
        #     self.__req_model.set_root_node(self.__root_node)
        #     self.__req_model.setHeaderData(0, QtCore.Qt.Horizontal, req_name)


# ---------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)

    req_agent = ReqSingleJsonFileAgent()
    req_agent.init()
    if not req_agent.open_req('Example'):
        req_agent.new_req('Example', True)
    w = RequirementUI(req_agent)

    w.show()
    sys.exit(app.exec_())


# ----------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass



