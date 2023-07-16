import faiss
import numpy as np
from typing import List, Dict, Any, Union, Tuple


# https://github.com/facebookresearch/faiss/wiki/Special-operations-on-indexes#removing-elements-from-an-index
# The method remove_ids removes a subset of vectors from an index. It takes an IDSelector object that is called for every element in the index to decide whether it should be removed. IDSelectorBatch will do this for a list of indices. The Python interface constructs this from numpy arrays if necessary.
#
# NB that since it does a pass over the whole database, this is efficient only when a significant number of vectors needs to be removed (see exception below).
#
# Example: test_index_composite.py
#
# Supported by IndexFlat, IndexIVFFlat, IDMap.
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

    def remove_ids(self, remove_ids: Union[int, List[int]]):
        if isinstance(remove_ids, int):
            remove_ids = [remove_ids]
        ids = np.array(remove_ids)
        self.index.remove_ids(ids)
        self.__remove_ids(remove_ids)
        if self.index is not faiss.IndexIVF and self.index is not faiss.IndexIDMap2:
            self.__shift_ids(remove_ids)

    def add_with_keys(self, data: List[List[float]], keys: List[Any]):
        if len(data) != len(keys):
            raise ValueError('data and keys are not the same length.')
        self.index.add(data)
        for k in keys:
            self.key_to_id[k] = self.next_id
            self.id_to_key[self.next_id] = k
            self.next_id += 1

    def remove_keys(self, keys: Union[str, List[str]]):
        if isinstance(keys, str):
            keys = [keys]
        remove_ids = [self.key_to_id[key] for key in keys if key in self.key_to_id.keys()]
        self.remove_ids(remove_ids)

    def search_by_key(self, xq: np.ndarray, k: int) -> List[Tuple[float, Any]]:
        vector = np.array([xq], dtype=np.float32)
        distance, indices = self.index.search(vector, k)
        score_keys = []
        for d, i in zip(distance[0], indices[0]):
            score_keys.append((d, self.id_to_key[i]))
        return score_keys

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

    result = index.search_by_key(data[0], 1)
    assert(result[0][1] == keys[0])

    result = index.search_by_key(data[2], 1)
    assert(result[0][1] == keys[2])

    result = index.search_by_key(data[4], 1)
    assert(result[0][1] == keys[4])

    # Remove not exists key should not cause error
    index.remove_keys([keys[1], keys[3]])
    assert(len(index.key_to_id) == 3)
    assert(len(index.id_to_key) == 3)

    # Remove the first one
    index.remove_keys(keys[0])

    assert(index.key_to_id[keys[2]] == 0)
    assert(index.key_to_id[keys[4]] == 1)

    result = index.search_by_key(data[2], 1)
    assert(result[0][1] == keys[2])

    result = index.search_by_key(data[4], 1)
    assert(result[0][1] == keys[4])

    # Remove the last one
    index.remove_keys(keys[4])

    assert (index.key_to_id[keys[2]] == 0)

    result = index.search_by_key(data[2], 1)
    assert (result[0][1] == keys[2])


test_keyfaiss_add_remove_search()


