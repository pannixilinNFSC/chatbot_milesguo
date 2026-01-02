import os
from openai import OpenAI # API v1.2
import json
import re
import pickle
import gzip
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter

import dotenv
dotenv.load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai_key)


    

def sentence_embedding_batch(txts, id):
    """Encode list of text to sentence embedding 1536 dimensions"""
    l1 = []
    #embs = get_embeddings(txts, engine="text-embedding-ada-002") # old api
    response = openai_client.embeddings.create(input = txts, model="text-embedding-ada-002")
    response = json.loads(response.json())["data"]
    embs = [x["embedding"] for x in response]
    for i, txt in enumerate(txts):
        label = f"{id}-{i}"
        emb = embs[i]
        l1.append((label, txt, emb))
    return l1

def encoding_file(in_file, output_dir):
    """Split document .txt file and encode to sentence embedding, compress and save as .npz file with same name"""
    id = os.path.basename(in_file).split(".")[0]
    out_file = os.path.join(output_dir, id+".npz")
    txts = load_data_to_paragraphs(in_file)
    packs = sentence_embedding_batch(txts, id)
    serialized_data = pickle.dumps(packs)
    compressed_data = gzip.compress(serialized_data)
    with open(out_file, "wb") as file:
        file.write(compressed_data)

def encoding_files(input_dir = "./txts/", output_dir = "./emb"):
    """Batch encode txt files in folder to embedding files with same name, 2866 files require OpenAI $3"""
    files = [os.path.join(input_dir, x) for x in os.listdir(input_dir)]
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    for i, in_file in enumerate(tqdm(files)):
        encoding_file(in_file, output_dir)

def decoding_file(file):
    with open(file, "rb") as f:
        compressed_data = f.read()
    decompressed_data = gzip.decompress(compressed_data)
    l1 = pickle.loads(decompressed_data)
    return l1
