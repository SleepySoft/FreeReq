from typing import Union, List

from FreeReq import IReqObserver, ReqNode


class IndexIdxAligned:
    def __init__(self):
        self.__any_index_idx_aligned = []
        self.__any_index_faiss_mapping = {}

    def item_add(self, index: any, idx: Union[int, List[int]]):
        if not isinstance(idx, list):
            idx = [idx]
        if index not in self.__any_index_faiss_mapping.keys():
            self.__any_index_faiss_mapping[index] = idx
            while
            self.__any_index_idx_aligned[idx] = index
        else:
            exists_idx = self.__any_index_faiss_mapping[index]
            exists_idx = list(set(exists_idx + idx))
            self.__any_index_faiss_mapping[index] = idx




class ChatReq(IReqObserver):
    def __init__(self):
        super().__init__()
        self.__req_uuid_idx_aligned = []
        self.__req_uuid_to_idx_mapping = {}

    def on_meta_data_changed(self, req_name: str):
        pass

    def on_node_data_changed(self, req_name: str, req_node: ReqNode):
        req_indices = self.__req_uuid_to_idx_mapping.get(req_node.get_uuid())

    def on_node_child_changed(self, req_name: str, req_node: ReqNode):
        pass


