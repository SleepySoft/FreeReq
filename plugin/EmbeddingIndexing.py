import torch
import faiss
from math import ceil
from typing import Dict, List, Tuple

from PyQt5.QtWidgets import QPushButton, QInputDialog
from text2vec import SentenceModel
from extra.KeyFaiss import KeyFaiss, DocumentKeyFaiss
from FreeReq import IReqAgent, RequirementUI, IReqObserver, ReqNode, STATIC_FIELD_CONTENT

# ----------------------------------------------------------------------------------------------------------------------

main_ui: RequirementUI = None

# ----------------------------------------------------------------------------------------------------------------------

# 查询向量数据库返回结果的最大数量
TOP_K = 5

EMBEDDING_DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# The embedding model name could be one of the following:
# Chinese:
#   ghuyong/ernie-3.0-nano-zh
#   nghuyong/ernie-3.0-base-zh
#   shibing624/text2vec-base-chinese
#   GanymedeNil/text2vec-large-chinese
# Common:
#   shibing624/text2vec-base-multilingual
# English:
#
EMBEDDING_MODEL_NAME = 'GanymedeNil/text2vec-large-chinese'


# ----------------------------------------------------------------------------------------------------------------------

def average_split_text(text: str, threshold: int, tolerance: float):
    if len(text) <= threshold * (1 + tolerance):
        return [text]
    else:
        n = ceil(len(text) / threshold)
        result = []
        for i in range(n):
            start = i * len(text) // n
            end = (i + 1) * len(text) // n
            result.append(text[start:end])
        return result


class EmbeddingIndexing(IReqObserver):
    def __init__(self, req: IReqAgent, split_threshold: int = 128):
        super().__init__()

        self.req_agent = req
        self.split_threshold = split_threshold

        self.embedding = SentenceModel(EMBEDDING_MODEL_NAME)

        embeddings = self.embedding.encode('Getting embedding length.')
        index = faiss.IndexFlatL2(len(embeddings))
        key_faiss = KeyFaiss(index)
        document_key_faiss = DocumentKeyFaiss(key_faiss)
        self.index = document_key_faiss

    def search(self, text: str, top_k: int = TOP_K) -> List[Tuple[float, str]]:
        search_embedding = self.embedding.encode(text)
        result = self.index.search(search_embedding, top_k)
        return result

    def on_req_reloaded(self):
        print('Indexing......')
        self.__reindex_all()
        print('Index all req complete.')

    def on_meta_data_changed(self, req_name: str):
        pass

    def on_node_data_changed(self, req_name: str, req_node: ReqNode):
        self.__index_node(req_node, False)

    def on_node_structure_changed(self, req_name: str, parent_node: ReqNode, child_node: List[ReqNode], operation: str):
        if operation == 'add':
            for node in child_node:
                self.__index_node(node, True)
        elif operation == 'remove':
            for node in child_node:
                self.__remove_node_index(node)
        else:
            pass

    # ---------------------------------------------------------------

    def __index_node(self, node: ReqNode, recursive: bool):
        title = node.get_title()
        content = node.get(STATIC_FIELD_CONTENT)
        node_text = (title if isinstance(title, str) else '') + \
                    (content if isinstance(content, str) else '')

        if len(node_text.strip()) == 0:
            return

        paragraph = average_split_text(node_text, self.split_threshold, 0.2)
        documents = self.embedding.encode(paragraph)
        self.index.update_document(documents, node.get_uuid())
        if recursive:
            for n in node.children():
                self.__index_node(n, True)

    def __reindex_all(self):
        self.index.reset()
        root_node = self.req_agent.get_req_root()
        self.__index_node(root_node, True)

    def __remove_node_index(self, node: ReqNode):
        self.index.remove_document(node.get_uuid())
        for n in node.children():
            self.__remove_node_index(n)


# ----------------------------------------------------------------------------------------------------------------------

req_agent: IReqAgent = None
emb_index: EmbeddingIndexing = None


# ----------------------------------------------------------------------------------------------------------------------

def search_req_nodes(text: str, top_k: int) -> List[ReqNode]:
    nodes = []
    result = emb_index.search(text, top_k)
    for distance, index in result:
        filter_nodes = req_agent.get_req_root().filter(lambda x: x.get_uuid() == index)
        nodes.extend(filter_nodes)
    return nodes


def on_embedding_search():
    text, ok = QInputDialog.getText(None, 'Search', 'Enter search text:')
    if ok:
        result = emb_index.search(text)

        default_index_window = main_ui.sub_window_index['default']
        default_index_window.clear_index()

        for distance, index in result:
            filter_nodes = req_agent.get_req_root().filter(lambda x: x.get_uuid() == index)
            if len(filter_nodes) > 0:
                default_index_window.append_index(filter_nodes[0].get_title(), filter_nodes[0].get_uuid())
                default_index_window.show_right_bottom()


# ----------------------------------------------------------------------------------------------------------------------


def plugin_prob() -> Dict[str, str]:
    return {
        'name': 'EmbeddingIndexing',
        'version': '1.0.0.0',
        'tags': 'embedding'
    }


def plugin_capacities() -> List[str]:
    return []


# ----------------------------------------------------------------------------------------------------------------------

def req_agent_prepared(req: IReqAgent):
    global req_agent
    global emb_index
    req_agent = req
    emb_index = EmbeddingIndexing(req)
    req_agent.add_observer(emb_index)


def after_ui_created(req_ui: RequirementUI):
    global main_ui
    main_ui = req_ui
    embedding_search_button = QPushButton('Embedding Search')
    main_ui.edit_board.layout_plugin_area.addWidget(embedding_search_button)
    embedding_search_button.clicked.connect(on_embedding_search)
