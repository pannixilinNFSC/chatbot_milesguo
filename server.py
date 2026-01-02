import os
import json
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from lib.rag.rag_base import RAGBase
from lib.app_logger import get_logger, setup_logging

app = FastAPI()
load_dotenv()
setup_logging()
logger = get_logger(__name__)
rag_base = RAGBase()

@app.get("/")
async def root():
    return {"message": "chatbot milesguo backend"}

@app.get("/version")
def version():
    return {"message": "v0.0.1"}

@app.get("/search_naive")
def search_naive(txt_query: str, k:int=10):
    try:
        search_results = rag_base.search_naive(txt_query, chunk_k=k)
        return search_results
    except RuntimeError as e:
        # Surface actionable config errors (e.g., missing API keys) to the caller.
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/search")
async def search(txt_query: str, title_k:int=3, chunk_k:int=10, expand_query:bool=True):
    try:
        search_results = await rag_base.search(
            txt_query, 
            title_k=title_k, 
            chunk_k=chunk_k, 
            expand_query=expand_query
        )
        return search_results
    except RuntimeError as e:
        # Surface actionable config errors (e.g., missing API keys) to the caller.
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/chatbot")
async def chatbot(txt_query: str, title_k:int=3, chunk_k:int=10, expand_query:bool=True):
    try:
        content, search_results, prompt = await rag_base.chat(
            txt_query, 
            title_k=title_k, 
            chunk_k=chunk_k, 
            expand_query=expand_query
        )
        return {
            "content": content,
            "search_results": search_results,
            "prompt": prompt,
        }
    except RuntimeError as e:
        # Surface actionable config errors (e.g., missing API keys) to the caller.
        raise HTTPException(status_code=500, detail=str(e)) from e

if __name__ == "__main__":
    #uvicorn.run(app, host="127.0.0.1", port=7711, ssl_keyfile="key.pem", ssl_certfile="certificate.pem")
    uvicorn.run(app, host="127.0.0.1", port=7711)
