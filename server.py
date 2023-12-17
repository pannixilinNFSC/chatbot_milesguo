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
    declaration = f"""
    网站声明

欢迎访问[爆料革命文库内容问答机器人]（以下简称"本网站"）！

网站目的：
本网站旨在通过数据检索和聊天机器人的形式帮助用户理解和检索以[郭文贵]先生直播的字幕内容为核心的，爆料革命和新中国联邦的核心文本。为用户提供易于访问和理解的信息，以促进知识的传播和共享。

代码开源：
本网站所有代码全部开源
https://github.com/pannixilinNFSC/chatbot_milesguo

数据来源：
本网站的全部检索内容来自于：https://gwins.org/

外部工具：
本网站调用openai sentence embedding ada-002 作为文本编码工具。
本网站调用openai chatgpt-3.5 作为文本生成模型。

免责声明：
本网站的内容仅供信息和参考之用，不构成法律、医疗、金融或其他专业建议。读者在使用本网站提供的信息时应谨慎，自行承担风险。本网站不对因使用本站内容而引发的任何后果承担责任。

隐私政策：
本网站尊重用户隐私，不会收集和分析用户ip地址和输入文本等信息。

作者信息：
本网站的内容由[盘尼西林]编写。[盘尼西林]是盖特工程师，GCLUB会员，已加入加拿大红叶农场。但开发此网站属于个人行为与任何公司或组织无关。

联系方式：
如果您有任何问题、建议或意见，欢迎通过以下方式与我联系：
- 社交媒体: https://gettr.com/user/pannixilin1

变更通知：
本网站声明的内容可能随时发生变更，变更后的声明将在本网站上公布。请定期查看以获取最新信息。
感谢您访问本网站，我们希望您能在这里找到有用的资源和信息！

[2023-12-17]
    """
    txt_response, txt_prompt = chatbot_utils.RAG_chatbot(txt_query, openai_client, txts_retrival, 
               prompt1=prompt1, prompt2=prompt2)
    json2 = [{i+1: f"题目：{title}\n 正文：{txt}" for i, (title, txt) in enumerate(txts_retrival)}]
    json1 = {"reply": txt_response, 
             "retrieval": json2, 
             "prompt": txt_prompt, 
             "declaration": declaration}
    return json1


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7711, ssl_keyfile="key.pem", ssl_certfile="certificate.pem")
