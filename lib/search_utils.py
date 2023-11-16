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

def build_faiss_index(embs):
    d = 1536
    nlist = 100  # 划分的聚类中心数量
    m = 32  # 每个向量的子编码数量
    k = 4  # 每个子编码的聚类中心数量
    index = faiss.IndexFlatIP(d) # 普通向量内积暴力检索索引
    #index = faiss.IndexIVFFlat(index, d, nlist) # 倒排索引
    #index = faiss.IndexIVFPQ(index, d, nlist, m, k)  # 建立IVFPQ索引
    index.train(embs)
    index.add(embs)
    return index

def build_vector_search_index(folder="./emb"):
    """构建向量检索索引和字典，充当向量数据库功能"""
    files = [os.path.join(folder, x) for x in os.listdir(folder)]
    dict_emb = dict()
    i = 0
    embs = []
    for file in tqdm(files):
        l1 = decoding_file(file)
        for idx, txt, emb in l1:
            dict_emb[i] = idx
            embs.append(emb)
            i+=1
    embs = np.vstack(embs)
    embs /= np.linalg.norm(embs, ord=2, axis=-1, keepdims=True) + 1e-8 # L2归一化
    faiss_index = build_faiss_index(embs)
    return embs, dict_emb, faiss_index

def load_text_from_idx(folder="./emb", idx=0):
    id = idx.split("-")[0]
    filename = os.path.join(folder, f"{id}.npz")
    l1 = decoding_file(filename)
    for idx1, txt, emb in l1:
        if idx1==idx:
            return txt
    return "not found"

def text_search(query, openai_client, faiss_index, dict_emb, dict_title, k=3):
    """ 
    用query文本，访问openai sentence embedding ada 002，得到句向量
    每1000个token(250汉字) 0.0001美元
    在向量索引中检索语音最相近的文档，并找对对应标题。
    """
    if len(query)<10:
        query = f"这是一段关于{query}的演讲"
    #emb_query = get_embedding(query, engine="text-embedding-ada-002")
    response = openai_client.embeddings.create(input=[query], model="text-embedding-ada-002")
    emb_query = json.loads(response.json())["data"][0]["embedding"]
    emb_query = np.array(emb_query).reshape((1, -1))
    D, I = faiss_index.search(emb_query, k)
    txts = []
    for i in I[0]:
        idx = dict_emb[i]
        idx0 = idx.split("-")[0]
        txt = load_text_from_idx("./emb", idx)
        title = dict_title[idx0]
        txts += [(title, txt)]
    return txts
