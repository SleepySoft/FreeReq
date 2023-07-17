from typing import Union, List
from FreeReq import IReqObserver, ReqNode


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


