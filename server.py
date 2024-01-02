import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.logger import logger
import lib.search_utils as search_utils
import lib.chatbot_utils as chatbot_utils
from openai import OpenAI # API v1.2

with open("./openai_key.txt", "r") as f:
    openai_key = f.read().strip()
    openai_client = OpenAI(api_key=openai_key)

app = FastAPI()
work_dir = "./"
search_client = search_utils.SearchClient(work_dir, openai_client)
chatbot_client = chatbot_utils.ChatbotClient(work_dir, openai_client)

work_dir_yi = "./liuzhongjing/"
search_client_yi = search_utils.SearchClient(work_dir_yi, openai_client)
chatbot_client_yi = chatbot_utils.ChatbotClient(work_dir_yi, openai_client)


@app.get("/")
async def root():
    return {"message": "chatbot milesguo backend"}

@app.get("/version")
def version():
    return {"message": "v0.0.1"}

@app.get("/search")
def search(txt_query: str, k:int=10):
    txts_retrival = search_client(txt_query, k=k) #请求10000次API成本1美金
    return txts_retrival

@app.get("/chatbot")
def chatbot(txt_query: str, k:int=3, prompt1:str=None, prompt2:str=None):
    txts_retrival = search_client(txt_query, k=k)
    json1 = chatbot_client(txt_query, txts_retrival, prompt1, prompt2)
    return json1

@app.get("/search_yi")
def search(txt_query: str, k:int=10):
    txts_retrival = search_client_yi(txt_query, k=k) #请求10000次API成本1美金
    return txts_retrival

@app.get("/chatbot_yi")
def chatbot(txt_query: str, k:int=3, prompt1:str=None, prompt2:str=None):
    txts_retrival = search_client_yi(txt_query, k=k)
    json1 = chatbot_client_yi(txt_query, txts_retrival, prompt1, prompt2)
    return json1

if __name__ == "__main__":
    #uvicorn.run(app, host="127.0.0.1", port=7711, ssl_keyfile="key.pem", ssl_certfile="certificate.pem")
    uvicorn.run(app, host="127.0.0.1", port=7711)
