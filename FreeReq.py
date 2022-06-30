from __future__ import annotations
import sys
import uuid
import traceback

try:
    # Use try catch for running FreeReq without UI

    from PyQt5 import QtCore
    from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem, QCursor
    from PyQt5.QtCore import pyqtSignal, Qt, QAbstractTableModel, QModelIndex, QRect, QVariant, QSize, QTimer, \
        QAbstractItemModel
    from PyQt5.QtWidgets import QMainWindow, QApplication, QHBoxLayout, QGridLayout, QWidget, QPushButton, \
        QDockWidget, QAction, qApp, QMessageBox, QDialog, QVBoxLayout, QLabel, QGroupBox, QTableWidget, \
        QTableWidgetItem, QTabWidget, QLayout, QTextEdit, QListWidget, QListWidgetItem, QMenu, QHeaderView, \
        QStyle, QStyleOptionButton, QTableView, QLineEdit, QCheckBox, QFileDialog, QComboBox, QTreeView, \
        QAbstractItemView
except Exception as e:
    print('UI disabled.')
    print(str(e))
finally:
    pass


CONST_FIELD_ID = 'id'
CONST_FIELD_UUID = 'uuid'
CONST_FIELD_TITLE = 'title'
CONST_FIELD_CHILD = 'child'

CONST_FIELDS = [CONST_FIELD_ID, CONST_FIELD_UUID, CONST_FIELD_TITLE, CONST_FIELD_CHILD]


class ReqNode:
    def __call__(self):
        return self

    def __init__(self, parent: ReqNode):
        self.__data = {
            CONST_FIELD_ID: '',
            CONST_FIELD_UUID: str(uuid.uuid4().hex),
            CONST_FIELD_TITLE: 'N/A',
            CONST_FIELD_CHILD: [],
        }
        self.__parent = parent
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
        self.__sibling = self.__parent.children if self.__parent is not None else []

    def add_child(self, node: ReqNode) -> int:
        self.__children.append(node)
        return len(self.__children) - 1

    def insert_sibling_left(self, node: ReqNode) -> int:
        index = self.order()
        self.__sibling.insert(self.order(), node)
        return index

    def insert_sibling_right(self, node: ReqNode) -> int:
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
                node = ReqNode(self)
                node.from_dict(sub_dict)
                self.__children.append(node)
            del self.__data[CONST_FIELD_CHILD]


class IReqObserver:
    def __init__(self):
        pass

    def on_node_updated(self, req_name, node_uuid: str, req_data: dict):
        pass


class IReqAgent:
    def __init__(self):
        self.__observer = None

    def init(self, *args, **kwargs) -> bool:
        pass

    def load_req_names(self) -> [str]:
        pass

    def load_req_meta(self, req_name: str) -> dict:
        pass

    def update_req_meta(self, req_name: str, req_meta: dict) -> bool:
        pass

    def load_req_root(self, req_name: str) -> dict:
        pass

    def update_req_root(self, req_name: str, req_root: dict) -> bool:
        pass

    def load_req_node(self, req_name: str, req_uuid: str) -> dict:
        pass

    def update_req_node(self, req_name: str, req_uuid: str, req_data: dict) -> bool:
        pass

    def set_observer(self, ob: IReqObserver):
        self.__observer = ob

    def notify_node_updated(self):
        if self.__observer is not None:
            self.__observer.on_node_updated()


class ReqXmlFileAgent(IReqAgent):
    def __init__(self):
        super(ReqXmlFileAgent, self).__init__()

    def init(self, *args, **kwargs) -> bool:
        pass

    def load_req_names(self) -> [str]:
        pass

    def load_req_meta(self, req_name: str) -> dict:
        pass

    def update_req_meta(self, req_name: str, req_meta: dict) -> bool:
        pass

    def load_req_root(self, req_name: str) -> dict:
        pass

    def update_req_root(self, req_name: str, req_root: dict) -> bool:
        pass

    def load_req_node(self, req_name: str, req_uuid: str) -> dict:
        pass

    def update_req_node(self, req_name: str, req_uuid: str, req_data: dict) -> bool:
        pass


class ReqModel(QAbstractItemModel):
    def __init__(self, root_node: ReqNode):
        super(ReqModel, self).__init__()

        self.__root_node = root_node

    # ------------------------------------- Method -------------------------------------

    def set_root_node(self, root_node: ReqNode):
        self.__root_node = root_node

    def get_root_node(self) -> ReqNode:
        return self.__root_node

    def get_node(self, index: QModelIndex) -> ReqNode:
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
        if parent is None or not parent.isValid():
            parent_item = self.__root_node
        else:
            parent_item: ReqNode = parent.internalPointer()

        if not QtCore.QAbstractItemModel.hasIndex(self, row, column, parent):
            return QModelIndex()

        child_item = parent_item.child(row)
        if child_item is not None:
            return QAbstractItemModel.createIndex(self, row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex = None):
        if index is None or not index.isValid():
            return QModelIndex()

        child_item: ReqNode = index.internalPointer()
        parent_item: ReqNode = child_item.parent()

        if parent_item is None:
            return QModelIndex()

        if parent_item == self.__root_node:
            return QtCore.QAbstractItemModel.createIndex(self, 0, 0, parent_item)
        row = parent_item.order()

        return QtCore.QAbstractItemModel.createIndex(self, row, 0, parent_item)

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs):
        if parent is None or not parent.isValid():
            parent_item = self.__root_node
        else:
            parent_item: ReqNode = parent.internalPointer()
        row_count = parent_item.child_count()

        return row_count

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs):
        # if parent.isValid():
        #     return len(parent.internalPointer().data())
        # return len(self.__root_node.data())
        return 1


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

# """
# QTreeView {
#     alternate-background-color: #f6fafb;
#     background: #e8f4fc;
# }
# QTreeView::item:open {
#     background-color: #c5ebfb;
#     color: blue;
# }
# QTreeView::item:selected {
#     background-color: #1d3dec;
#     color: white;
# }
# QTreeView::branch {
#     background-color: white;
# }
# QTreeView::branch:open {
#     image: url(branch-open.png);
# }
# QTreeView::branch:closed:has-children {
#     image: url(branch-closed.png);
# }
# """


class RequirementUI(QWidget):
    def __init__(self, req_data_agent: IReqAgent):
        super(RequirementUI, self).__init__()

        self.__root_node = ReqNode(None)
        self.__req_data_agent = req_data_agent
        self.__req_model = ReqModel(self.__root_node)
        self.__menu_on_node: ReqNode = None
        self.__menu_on_index: ReqNode = None

        self.__tree_requirements = QTreeView()
        self.__text_md_editor = QTextEdit()
        self.__text_md_preview = QTextEdit()
        self.__group_meta_data = QGroupBox()

        self.__init_ui()
        self.refresh_data()

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
        self.__tree_requirements.setStyleSheet(TREE_VIEW_STYLE_SHEET)
        self.__tree_requirements.setAlternatingRowColors(True)
        self.__tree_requirements.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__tree_requirements.customContextMenuRequested.connect(self.on_requirement_tree_menu)

    def on_requirement_tree_menu(self, pos: QPoint):
        sel_index: QModelIndex = self.__tree_requirements.indexAt(pos)
        if sel_index is not None and sel_index.isValid():
            self.__menu_on_index = sel_index
            self.__menu_on_node = self.__req_model.get_node(sel_index)

            menu = QMenu()
            menu.addAction('Append Child', self.on_requirement_tree_menu_add_child)
            menu.addSeparator()
            menu.addAction('Insert sibling up', self.on_requirement_tree_menu_add_sibling_up)
            menu.addAction('Insert sibling down', self.on_requirement_tree_menu_add_sibling_down)
            menu.exec(QCursor.pos())
        else:
            self.__menu_on_node = None

    def on_requirement_tree_menu_add_child(self):
        if self.__menu_on_node is not None:
            self.__req_model.layoutAboutToBeChanged.emit()
            new_node = ReqNode(self.__menu_on_node)
            self.__menu_on_node.add_child(new_node)
            self.__req_model.layoutChanged.emit()

    def on_requirement_tree_menu_add_sibling_up(self):
        if self.__menu_on_node is not None:
            pass

    def on_requirement_tree_menu_add_sibling_down(self):
        if self.__menu_on_node is not None:
            pass

    def refresh_data(self):
        for c in 'ABCDEFG':
            sub_node = ReqNode(self.__root_node)
            sub_node.set_title(c)
            self.__root_node.add_child(sub_node)
        self.__root_node.set_title('Root')
        self.__req_model = ReqModel(self.__root_node)
        self.__tree_requirements.setModel(self.__req_model)


# ---------------------------------------------------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    w = RequirementUI(ReqXmlFileAgent())
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



