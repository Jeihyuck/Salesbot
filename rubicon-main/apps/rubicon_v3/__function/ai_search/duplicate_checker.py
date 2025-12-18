import numpy as np
from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_similarity


from typing import List, Optional


class DuplicateChecker:
    """중복 체크를 위한 클래스"""

    def __init__(
        self,
        threshold: float,
        embedding_list: Optional[List[NDArray[np.float32]]] = None,
    ):
        if embedding_list is None:
            self.embedding_list = []
        else:
            self.embedding_list = embedding_list
        self.threshold = threshold
        self.msg_set = set()

    def _is_duplicate(self, embedding: NDArray[np.float32]) -> bool:
        """임베딩이 중복인지 확인"""
        for eb in self.embedding_list:
            sim = cosine_similarity(eb.reshape(1, -1), embedding.reshape(1, -1))[0, 0]
            if sim > self.threshold:
                return True
        return False

    def __len__(self):
        return len(self.embedding_list)

    def append_embedding(self, embedding: NDArray[np.float32]):
        """임베딩을 리스트에 추가

        Returns:
            True: 추가 성공
        """
        if not self._is_duplicate(embedding):
            self.embedding_list.append(embedding)
            return True
        else:
            return False

    def append_with_key(self, msg):
        key = msg.strip().replace(" ", "").lower() if msg and isinstance(msg, str) else None
        if key in self.msg_set:
            return False
        
        self.msg_set.add(key)
        return True