import os
import json
import re
import pickle
import numpy as np
from tqdm import tqdm
import jieba
import gzip
from lib.search_utils import *
from rank_bm25 import BM25Okapi


def build_bm25(emb_dir):
    files = [os.path.join(emb_dir, x) for x in os.listdir(emb_dir)]
    tokenized_corpus = []
    labels = []
    for filename in tqdm(sorted(files)):
        l1 = decoding_file(filename)
        for label, txt, emb in l1:
            corpus = list(jieba.cut(txt))
            tokenized_corpus.append(corpus)
            labels.append(label)
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, labels

def text_search_bm25(query, bm25, labels, k):
    tokenized_query = list(jieba.cut(query))
    scores = bm25.get_scores(tokenized_query)
    indices = np.argsort(-scores)[:k]
    labels = [labels[idx] for idx in indices]
    return labels

class SearchClientBM25(object):
    def __init__(self, work_dir, force_rebuild=False):
        emb_dir = os.path.join(work_dir, "emb")
        index_path = os.path.join(work_dir, 'bm25.index')
        title_path = os.path.join(work_dir, "titles.json")
        self.work_dir = work_dir
        self.dict_title = load_titles(file=title_path) # 读取标题文件
        if force_rebuild or not os.path.isfile(index_path):
            bm25, labels = build_bm25(emb_dir)
            with open(index_path, "wb") as f:
                pickle.dump((bm25, labels), f)
        with open(index_path, "rb") as f:
            bm25, labels = pickle.load(f)
        self.bm25 = bm25
        self.labels = labels
        
    def query_label(self, query, k=3):
        return text_search_bm25(query, self.bm25, self.labels, k=k)
        
    def __call__(self, query, k=3):
        labels = self.query_label(query, k)
        txts = label2texts(labels, self.dict_title, work_dir=self.work_dir)
        return txts
    
def RRF(labels_list, k=3):
    """Reciprocal Rank Fusion"""
    k0 = np.max([len(l1) for l1 in labels_list])
    labels = list(set(sum(labels_list, [])))
    dicts = [{x:i for i,x in enumerate(labels1)} for labels1 in labels_list]
    scores = []
    debug = []
    for x in labels:
        l1 = []
        for dict1 in dicts:
            i1 = dict1.get(x, k0*2)
            l1.append(i1)
        debug.append(l1)
        score = sum([1/(idx+60) for idx in l1])
        scores.append(score)
    rank = np.argsort(-np.float32(scores))[:k]
    labels = [labels[i] for i in rank]
    print([debug[i] for i in rank])
    return labels
    
        
class SearchClientHybrid(object):
    def __init__(self, work_dir, openai_client, force_rebuild=False):
        self.sc_emb = SearchClient(work_dir, openai_client, force_rebuild)
        self.sc_word = SearchClientBM25(work_dir, force_rebuild)
        
    def __call__(self, query, k=3, k0=500):
        labels1 = self.sc_emb.query_label(query, k=k0)
        labels2 = self.sc_word.query_label(query, k=k0)
        labels = RRF([labels1, labels2], k)
        txts = label2texts(labels, self.sc_emb.dict_title, work_dir=self.sc_emb.work_dir)
        return txts
        
    
if __name__ == "__main__":
    with open("./openai_key.txt", "r") as f:
        openai_key = f.read().strip()
    openai_client = OpenAI(api_key=openai_key)
    #search_client = SearchClientBM25("./lzj_official/")
    search_client = SearchClientHybrid("./lzj_official/", openai_client)
    query = "郭文贵是谁"
    txts = search_client(query, k=2)
    print(txts)