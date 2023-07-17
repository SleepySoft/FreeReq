from typing import Dict, List

import faiss
from math import ceil
from text2vec import SentenceModel
from plugin.KeyFaiss import KeyFaiss, DocumentKeyFaiss
from FreeReq import IReqAgent, RequirementUI, IReqObserver, ReqNode, STATIC_FIELD_CONTENT

# ----------------------------------------------------------------------------------------------------------------------

# 查询向量数据库返回结果的最大数量
TOP_K = 5

EMBEDDING_DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# The embedding model name could be one of the following:
#   ghuyong/ernie-3.0-nano-zh
#   nghuyong/ernie-3.0-base-zh
#   shibing624/text2vec-base-chinese
#   GanymedeNil/text2vec-large-chinese
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

        index = faiss.IndexFlatL2(self.embedding.encode('Getting embedding length.'))
        key_faiss = KeyFaiss(index)
        document_key_faiss = DocumentKeyFaiss(key_faiss)
        self.index = document_key_faiss

    def on_req_reloaded(self):
        self.__reindex_all()

    def on_meta_data_changed(self, req_name: str):
        pass

    def on_node_data_changed(self, req_name: str, req_node: ReqNode):
        self.__index_node(req_node, False)

    def on_node_structure_changed(self, req_name: str, parent_node: ReqNode, child_node: ReqNode, operation: str):
        if operation == 'add':
            self.__index_node(child_node, False)
        elif operation == 'remove':
            self.index.remove_document(child_node.get_uuid())
        else:
            pass

    # ---------------------------------------------------------------

    def __index_node(self, node: ReqNode, recursive: bool):
        node_text = node.get_title() + node.get(STATIC_FIELD_CONTENT)
        if len(node_text.strip()) == 0:
            return
        paragraph = average_split_text(node_text, self.split_threshold, 0.2)
        documents = [self.embedding.encode(p) for p in paragraph]
        self.index.update_document(documents, node.get_uuid())
        if recursive:
            for n in node.children():
                self.__index_node(n, True)

    def __reindex_all(self):
        self.index.reset()
        root_node = self.req_agent.get_req_root()
        self.__index_node(root_node, True)


# ----------------------------------------------------------------------------------------------------------------------


def plugin_prob() -> Dict[str, str]:
    return {
        'name': 'Embedding Indexing',
        'version': '1.0.0.0',
        'tags': 'embedding'
    }


def plugin_capacities() -> List[str]:
    return []


# ----------------------------------------------------------------------------------------------------------------------

req_agent = None


def req_agent_prepared(req: IReqAgent):
    global req_agent
    req_agent = req
    req_agent.add_observer()


def after_ui_created(req_ui: RequirementUI):
    pass

