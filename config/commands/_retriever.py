
import math
import numpy as np
import sys
from typing import list

class BM25Retriever:
    def __init__(self, docs: list[str], search_level: str):
        self.search_level = search_level
        self.documents = self.load_documents()
        self.D = len(docs)
        self.avg_len = sum([len(doc) + 0.0 for doc in docs]) / self.D
        self.docs = docs
        self.f = []  # Each element of the list is a dictionary, and the dictionary stores the occurrence count of each word in a document 列表的每一个元素是一个dict，dict存储着一个文档中每个词的出现次数
        self.df = {}  # Store each word and the number of documents in which the word appears. 存储每个词及出现了该词的文档数量
        self.idf = {}  # 存储每个词的idf值
        self.k1 = 1.5
        self.b = 0.75
        self.init()
    
    def init(self):
        for doc in self.docs:
            doc = doc.lower().split()
            tmp = {}
            for word in doc:
                tmp[word] = tmp.get(word, 0) + 1  # 存储每个文档中每个词的出现次数
            self.f.append(tmp)
            for k in tmp.keys():
                self.df[k] = self.df.get(k, 0) + 1
        for k, v in self.df.items():
            self.idf[k] = math.log(self.D - v + 0.5) - math.log(v + 0.5)

        
    def sim(self, doc, index):
        score = 0
        for word in doc:
            if word not in self.f[index]:
                continue
            d = len(self.docs[index])
            score += (self.idf[word] * self.f[index][word] * (self.k1 + 1)
                      / (self.f[index][word] + self.k1 * (1 - self.b + self.b * d / self.avg_len)))
        return score

    def compute_scores(self, keywords: list[str]):
        scores = []
        for i in range(self.D):
            score = self.sim(keywords, i)
            scores.append(score)
        return scores


    def load_documents(self):
        # Dummy documents for illustration. Replace with actual document loading logic.
        return [
            {"doc_id": 1, "text": "This is a sample document for BM25 retrieval."},
            {"doc_id": 2, "text": "Another example document for testing BM25 retrieval."},
        ]

    def retrieve(self, query):
        # Dummy implementation for illustration. Replace with actual BM25 retrieval logic.
        results = []
        for doc in self.documents:
            if query.lower() in doc["text"].lower():
                results.append(doc["doc_id"])
        return results
    
    def rough_sort(self, keywords: list[str], answers: list[str], top_k=100) -> list[str]:
        scores = self.compute_scores(keywords)
        top_k_idx = np.array(scores).argsort()[-top_k:][::-1]
        return [answers[idx] for idx in top_k_idx]

def main(search_level: str, query: str):
    retriever = BM25Retriever(search_level)
    results = retriever.retrieve(query)
    for result in results:
        print(result)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python _retriever.py <search_level> <query>")
        sys.exit(1)
    
    search_level = sys.argv[1]
    query = sys.argv[2]
    main(search_level, query)