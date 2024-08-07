
import math
import numpy as np
import sys
import os
from typing import List, Tuple


class BM25Retriever:
    def __init__(self, docs: List[str]):
        self.D = len(docs)
        self.avg_len = sum([len(doc.split()) for doc in docs]) / self.D
        self.docs = docs
        self.f = []  # Term frequency for each document
        self.df = {}  # Document frequency of terms
        self.idf = {}  # Inverse document frequency
        self.k1 = 1.5
        self.b = 0.75
        self.init()

    def init(self):
        for doc in self.docs:
            words = doc.lower().split()
            tmp = {}
            for word in words:
                tmp[word] = tmp.get(word, 0) + 1
            self.f.append(tmp)
            for k in tmp.keys():
                self.df[k] = self.df.get(k, 0) + 1
        for k, v in self.df.items():
            self.idf[k] = math.log(self.D - v + 0.5) - math.log(v + 0.5)

    def sim(self, query: List[str], index: int) -> float:
        score = 0
        for word in query:
            if word not in self.f[index]:
                continue
            d = len(self.docs[index].split())
            score += (self.idf[word] * self.f[index][word] * (self.k1 + 1) /
                      (self.f[index][word] + self.k1 * (1 - self.b + self.b * d / self.avg_len)))
        return score

    def compute_scores(self, keywords: List[str]) -> List[float]:
        scores = []
        for i in range(self.D):
            score = self.sim(keywords, i)
            scores.append(score)
        return scores

    def retrieve(self, keywords: List[str], files: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        scores = self.compute_scores(keywords)
        top_k_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(files[idx], scores[idx]) for idx in top_k_idx]

def load_documents(directory: str) -> Tuple[List[str], List[str]]:
    docs = []
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py'):  # Only process Python files
                filepath = os.path.join(root, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    docs.append(f.read())
                    files.append(filepath)
    return docs, files

def main(directory: str, query: str, top_k: int):
    docs, files = load_documents(directory)
    retriever = BM25Retriever(docs)
    query_keywords = query.lower().split()

    results = retriever.retrieve(query_keywords, files, top_k=top_k)
    for file_path, score in results:
        print(f"{file_path}: {score:.3f}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python bm25_retriever.py <directory> <keywords> <topn>")
        sys.exit(1)
    
    directory = sys.argv[1]
    query = sys.argv[2]
    top_n = int(sys.argv[3])
    main(directory, query, top_n)

