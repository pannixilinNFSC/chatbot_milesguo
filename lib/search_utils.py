import os
import json
import re
import faiss
import pickle
import gzip
import numpy as np
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
import openai
from openai import OpenAI # API v1.2

def load_titles(file="title.json"):
    """Load the titles mapping JSON file."""
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
    nlist = 100  # Number of IVF clusters (only used if you enable IVF indexes below).
    m = 32  # Number of PQ sub-vectors (only used if you enable IVFPQ below).
    k = 4  # Number of centroids per PQ sub-vector (only used if you enable IVFPQ below).
    embs = embs[:,:512]
    embs /= np.linalg.norm(embs, ord=2, axis=-1, keepdims=True)
    # Baseline: brute-force inner-product search (fast enough for smaller corpora).
    index = faiss.IndexFlatIP(d)
    # index = faiss.IndexIVFFlat(index, d, nlist)  # IVF (inverted file) index
    # index = faiss.IndexIVFPQ(index, d, nlist, m, k)  # IVF+PQ index
    #index.train(embs)
    index.add(embs)
    return index

def build_vector_search_index(folder="./emb"):
    """Build a FAISS index plus an id->label mapping (a lightweight vector DB)."""
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
    # L2-normalize so inner product approximates cosine similarity.
    embs /= np.linalg.norm(embs, ord=2, axis=-1, keepdims=True) + 1e-8
    faiss_index = build_faiss_index(embs)
    return embs, dict_emb, faiss_index

def text_search_emb(query, openai_client, faiss_index, dict_emb, k=3):
    """ 
    Embed the query via OpenAI embeddings and retrieve the nearest documents from FAISS.

    Notes:
    - Embedding cost depends on token usage and the selected model (see OpenAI pricing).
    - We search in vector space and then map vector ids back to document labels/titles.
    """
    if len(query)<10:
        query = f"This is a speech about {query}"
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
            # Read embedding files and (re)build the FAISS index on demand.
            embs, dict_emb, faiss_index = build_vector_search_index(folder=emb_dir)
            del embs
            faiss.write_index(faiss_index, index_path)
            with open(dict_emb_path, "w") as f:
                json.dump(dict_emb, f)
        
        faiss_index = faiss.read_index(index_path)
        with open(dict_emb_path, "r") as f:
            dict_emb = {int(k):v for k, v in json.load(f).items()}
        dict_title = load_titles(file=title_path)  # Load title mapping.
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
            query = f"This is a text about {query}"
        labels = self.query_label(query, k)
        txts = label2texts(labels, self.dict_title, work_dir=self.work_dir)
        return txts