import os
from lib.openai_utils import openai_client
import lib.search_utils as search_utils
import lib.chatbot_utils as chatbot_utils
import uvicorn
import faiss
import json


from fastapi import FastAPI, Request, HTTPException
from fastapi.logger import logger

app = FastAPI()
faiss_index = faiss.read_index("my_index.index")
with open("dict_emb.json", "r") as f:
    dict_emb = {int(k):v for k, v in json.load(f).items()}
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


@app.get("/chatbot")
def chatbot(txt_query: str, k:int=3, prompt1:str=None, prompt2:str=None):
    txts_retrival = search_utils.text_search(txt_query, openai_client, faiss_index, dict_emb, dict_title, k=k)
    if prompt1 is None:
        prompt1 = f"""你需要全面地总结和转述参考文本中与给出的话题相关的部分。
内容尽量丰富，语言生动，充满细节。
并总结与以下话题有关的内容。话题是："""
    if prompt2 is None:
        prompt2 = f"""\n你不能评价其中的内容，并且需要忽略与此话题无关的内容。
如果内容出现了矛盾和冲突，以时间靠后的内容为准。
你需要在转述结束后引导用户向你提出进一步这个话题相关的不同问题。如您还可以问我xxx\n
以下是参考文本\n"""
    txt_response, txt_prompt = chatbot_utils.RAG_chatbot(txt_query, openai_client, txts_retrival, 
               prompt1=prompt1, prompt2=prompt2)
    json2 = [{i+1: f"题目：{title}\n 正文：{txt}" for i, (title, txt) in enumerate(txts_retrival)}]
    json1 = {"reply": txt_response, 
             "retrieval": json2, 
             "prompt": txt_prompt}
    return json1


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7711, ssl_keyfile="key.pem", ssl_certfile="certificate.pem")
