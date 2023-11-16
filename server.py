import os
from lib.openai_utils import openai_client
import lib.search_utils as search_utils
import lib.chatbot_utils as chatbot_utils
import uvicorn


from fastapi import FastAPI, Request, HTTPException
from fastapi.logger import logger

app = FastAPI()
embs, dict_emb, faiss_index = search_utils.build_vector_search_index(folder="./emb") # 读取编码文件，构建向量索引
dict_title = search_utils.load_titles(file="titles.json") # 读取标题文件

@app.get("/")
async def root():
    return {"message": "chatbot milesguo backend"}

@app.get("/version")
def version():
    return {"message": "v0.0.1"}

@app.get("/search")
def search(txt_query: str):
    txts_retrival = search_utils.text_search(txt_query, openai_client, faiss_index, dict_emb, dict_title, k=3) #请求10000次API成本1美金
    return txts_retrival

"""
@app.get("/chatbot")
def chatbot(txt_query: str):
    txts_retrival = search_utils.text_search(txt_query, openai_client, faiss_index, dict_emb, dict_title, k=3)
    txt_response = chatbot_utils.RAG_chatbot(txt_query, openai_client, txts_retrival, 
                prompt1="你需要全面地摘要并总结a所有参考文本，并总结对以下问题的回答：", 
                prompt2="以下是参考文本\n\n")
    txt_all = ""
    txt_all += txt_response
    txt_all += "以下是检索得到的原始参考文本"
    for i, (title, txt) in enumerate(txts_retrival):
        txt_all += f"{i+1}. {title}"
        txt_all += txt
    return txt_all
"""

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7711, ssl_keyfile="key.pem", ssl_certfile="certificate.pem")
