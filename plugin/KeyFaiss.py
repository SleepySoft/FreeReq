import traceback
import uuid

import faiss
import numpy as np
from typing import List, Dict, Any, Union, Tuple


# https://github.com/facebookresearch/faiss/wiki/Special-operations-on-indexes#removing-elements-from-an-index
#
# Note that there is a semantic difference when removing ids from sequential indexes vs. when removing them from an IndexIVF:
#
# for sequential indexes (IndexFlat, IndexPQ, IndexLSH), the removal operation shifts the ids of vectors above the removed vector id.
#
# the IndexIVF and IndexIDMap2 store the ids of vectors explicitly, so the ids of other vectors are not changed. There are two special cases for IndexIVF:
#
# DirectMap type Array does not support removal because it means that all the indices would be shifted, which does not seem very useful.
# with a direct map type Hashtable and a selector IDSelectorArray elements can be removed without scanning the whole index.


class KeyFaiss:
    def __init__(self, index: faiss.Index):
        self.index = index
        self.key_to_id = {}
        self.id_to_key = {}
        self.next_id = 0

    def search(self, xq: np.ndarray, k: int) -> List[Tuple[float, Any]]:
        vector = np.array([xq], dtype=np.float32)
        distance, indices = self.index.search(vector, k)
        distance_key = []
        for d, i in zip(distance[0], indices[0]):
            distance_key.append((d, self.id_to_key[i]))
        return distance_key

    def add_with_keys(self, data: List[List[float]], keys: List[Any]):
        if len(data) != len(keys):
            raise ValueError('data and keys are not the same length.')
        self.index.add(data)
        for k in keys:
            self.key_to_id[k] = self.next_id
            self.id_to_key[self.next_id] = k
            self.next_id += 1

    def remove_ids(self, remove_ids: Union[int, List[int]]):
        if isinstance(remove_ids, int):
            remove_ids = [remove_ids]
        ids = np.array(remove_ids)
        self.index.remove_ids(ids)
        self.__remove_ids(remove_ids)
        if self.index is not faiss.IndexIVF and self.index is not faiss.IndexIDMap2:
            self.__shift_ids(remove_ids)

    def remove_keys(self, keys: Union[str, List[str]]):
        if isinstance(keys, str):
            keys = [keys]
        remove_ids = [self.key_to_id[key] for key in keys if key in self.key_to_id.keys()]
        self.remove_ids(remove_ids)

    # ---------------------------------------------------------------

    def __remove_ids(self, remove_ids: Union[int, List[int]]):
        # 如果remove_ids是一个整数，将其转换为列表
        if isinstance(remove_ids, int):
            remove_ids = [remove_ids]
        # 对于每个要删除的id
        for remove_id in remove_ids:
            # 从self.id_to_key中弹出该id，并获取对应的键
            key = self.id_to_key.pop(remove_id)
            # 从self.key_to_id中删除相应的项
            del self.key_to_id[key]

    def __shift_ids(self, removed_ids: Union[int, List[int]]):
        # 如果removed_ids是一个整数，将其转换为列表
        if isinstance(removed_ids, int):
            removed_ids = [removed_ids]
        # 对removed_ids进行降序排序
        removed_ids.sort(reverse=True)
        # 对于每个已删除的id
        for removed_id in removed_ids:
            max_id = max(self.id_to_key.keys())
            for i in range(removed_id + 1, max_id + 1):
                key = self.id_to_key.pop(i)
                self.id_to_key[i - 1] = key
                self.key_to_id[key] = i - 1


# ----------------------------------------------------------------------------------------------------------------------

class DocumentKeyFaiss:
    def __init__(self, index: KeyFaiss):
        self.index = index
        self.ext_key_to_int_key = {}
        self.int_key_to_ext_key = {}

    def add_document(self, data: Union[List[float], List[List[float]]], key: Any):
        if not isinstance(data, list):
            return
        if not isinstance(data[0], list):
            data = [data]

        internal_keys = [str(uuid.uuid4().hex) for _ in data]
        self.index.add_with_keys(data, internal_keys)

        for k in internal_keys:
            self.int_key_to_ext_key[k] = key
        self.ext_key_to_int_key[key] = internal_keys

    def remove_document(self, key: Any):
        if key not in self.ext_key_to_int_key.keys():
            return
        internal_keys = self.ext_key_to_int_key[key]

        self.index.remove_keys(internal_keys)

        for k in internal_keys:
            del self.int_key_to_ext_key[k]
        del self.ext_key_to_int_key[key]

    def search(self, xq: np.ndarray, k: int) -> List[Tuple[float, Any]]:
        result = self.index.search(xq, k)

        refactor_result = {}
        for distance, key in result:
            if key not in refactor_result or distance < refactor_result[key]:
                refactor_result[key] = distance
        sorted_result = sorted(refactor_result.items(), key=lambda x: x[1])
        return [(v, k) for k, v in sorted_result]


# ----------------------------------------------------------------------------------------------------------------------

def test_keyfaiss_add_remove_search():
    d = 64
    raw_index = faiss.IndexFlatL2(d)
    index = KeyFaiss(raw_index)
    data = np.random.random((5, d)).astype('float32')
    keys = ['a', 'b', 'c', 'd', 'e']

    index.add_with_keys(data, keys)

    assert index.key_to_id == {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4}
    assert index.id_to_key == {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e'}

    # Remove key and verify key shift
    index.remove_keys([keys[1], keys[3]])

    assert(index.key_to_id[keys[0]] == 0)
    assert(index.key_to_id[keys[2]] == 1)
    assert(index.key_to_id[keys[4]] == 2)

    result = index.search(data[0], 1)
    assert(result[0][1] == keys[0])

    result = index.search(data[2], 1)
    assert(result[0][1] == keys[2])

    result = index.search(data[4], 1)
    assert(result[0][1] == keys[4])

    # Remove not exists key should not cause error
    index.remove_keys([keys[1], keys[3]])
    assert(len(index.key_to_id) == 3)
    assert(len(index.id_to_key) == 3)

    # Remove the first one
    index.remove_keys(keys[0])

    assert(index.key_to_id[keys[2]] == 0)
    assert(index.key_to_id[keys[4]] == 1)

    result = index.search(data[2], 1)
    assert(result[0][1] == keys[2])

    result = index.search(data[4], 1)
    assert(result[0][1] == keys[4])

    # Remove the last one
    index.remove_keys(keys[4])

    assert (index.key_to_id[keys[2]] == 0)

    result = index.search(data[2], 1)
    assert (result[0][1] == keys[2])


# ---------------------------------------------------------------------------------------------------------------------

def main():
    test_keyfaiss_add_remove_search()


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
