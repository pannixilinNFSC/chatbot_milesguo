import os
import json
import re
import faiss
import pickle
import gzip
import numpy as np
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
import openai
from openai import OpenAI # API v1.2

def load_titles(file="title.json"):
    """读取标题文件"""
    with open(file, "r") as f:
        dict1 = json.load(f)
    return dict1

def decoding_file(file):
    with open(file, "rb") as f:
        compressed_data = f.read()
    decompressed_data = gzip.decompress(compressed_data)
    l1 = pickle.loads(decompressed_data)
    return l1

def load_text_from_idx(folder="./emb", label=0):
    file_name = "-".join(label.split("-")[:-1])
    filename = os.path.join(folder, f"{file_name}.npz")
    l1 = decoding_file(filename)
    for label1, txt, emb in l1:
        if label1==label:
            return txt
    return "not found"

def build_faiss_index(embs):
    d = 512
    nlist = 100  # 划分的聚类中心数量
    m = 32  # 每个向量的子编码数量
    k = 4  # 每个子编码的聚类中心数量
    embs = embs[:,:512]
    embs /= np.linalg.norm(embs, ord=2, axis=-1, keepdims=True)
    index = faiss.IndexFlatIP(d) # 普通向量内积暴力检索索引
    #index = faiss.IndexIVFFlat(index, d, nlist) # 倒排索引
    #index = faiss.IndexIVFPQ(index, d, nlist, m, k)  # 建立IVFPQ索引
    #index.train(embs)
    index.add(embs)
    return index

def build_vector_search_index(folder="./emb"):
    """构建向量检索索引和字典，充当向量数据库功能"""
    print("building vector search index")
    files = [os.path.join(folder, x) for x in os.listdir(folder)]
    dict_emb = dict()
    global_index = 0
    embs = []
    for file in tqdm(sorted(files)):
        l1 = decoding_file(file)
        for label, txt, emb in l1:
            emb = np.float16(emb)
            dict_emb[global_index] = label # label = f"{file_name}-{idx}"
            embs.append(emb)
            global_index +=1
    embs = np.vstack(embs)
    embs /= np.linalg.norm(embs, ord=2, axis=-1, keepdims=True) + 1e-8 # L2归一化
    faiss_index = build_faiss_index(embs)
    return embs, dict_emb, faiss_index

def text_search_emb(query, openai_client, faiss_index, dict_emb, k=3):
    """ 
    用query文本，访问openai sentence embedding ada 002，得到句向量
    每1000个token(250汉字) 0.0001美元
    在向量索引中检索语音最相近的文档，并找对对应标题。
    """
    if len(query)<10:
        query = f"这是一段关于{query}的演讲"
    #emb_query = get_embedding(query, engine="text-embedding-ada-002")
    model="text-embedding-3-small"
    emb_query = openai_client.embeddings.create(input=[query], model=model).data[0].embedding
    emb_query = np.array(emb_query[:512]).reshape((1, -1))
    emb_query /= np.linalg.norm(emb_query, ord=2, axis=-1, keepdims=True)
    D, I = faiss_index.search(emb_query, k)
    labels = [dict_emb[i] for i in I[0]]
    return labels

def label2texts(labels, dict_title, work_dir="./"):
    txts = []
    for label in labels:
        file_name = "-".join(label.split("-")[:-1])
        folder = os.path.join(work_dir, "./emb")
        txt = load_text_from_idx(folder, label)
        title = dict_title[file_name]
        txts += [(title, txt)]
    return txts

class SearchClient(object):
    def __init__(self, work_dir, openai_client, force_rebuild=False):
        emb_dir = os.path.join(work_dir, "emb")
        title_path = os.path.join(work_dir, "titles.json")
        index_path = os.path.join(work_dir, 'my_index.index')
        dict_emb_path = os.path.join(work_dir, "dict_emb.json")
        if force_rebuild or not os.path.isfile(index_path) or not os.path.isfile(dict_emb_path):
            embs, dict_emb, faiss_index = build_vector_search_index(folder=emb_dir) # 读取编码文件，构建向量索引
            del embs
            faiss.write_index(faiss_index, index_path)
            with open(dict_emb_path, "w") as f:
                json.dump(dict_emb, f)
        
        faiss_index = faiss.read_index(index_path)
        with open(dict_emb_path, "r") as f:
            dict_emb = {int(k):v for k, v in json.load(f).items()}
        dict_title = load_titles(file=title_path) # 读取标题文件
        self.dict_emb = dict_emb
        self.dict_title = dict_title
        self.faiss_index = faiss_index
        self.openai_client = openai_client
        self.work_dir = work_dir
        
    def query_label(self, query, k=3):
        labels = text_search_emb(query, self.openai_client, self.faiss_index, self.dict_emb, k=k)
        return labels
        
    def __call__(self, query, k=3):
        if len(query)<10:
            query = f"这是一段关于{query}的文本"
        labels = self.query_label(query, k)
        txts = label2texts(labels, self.dict_title, work_dir=self.work_dir)
        return txts