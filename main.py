import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Query
from dotenv import load_dotenv
from lib.rag.rag_base import RAGBase
from lib.app_logger import get_logger, setup_logging
from lib.security import setup_cors, require_auth, require_rate_limit, global_exception_handler

app = FastAPI()
load_dotenv()
setup_logging()
logger = get_logger(__name__)
rag_base = RAGBase()

setup_cors(app)
app.add_exception_handler(Exception, global_exception_handler)

@app.get("/")
async def root():
    return {"message": "chatbot milesguo backend"}

@app.get("/version")
def version():
    return {"message": "v0.0.1"}

@app.get("/token")
def get_token():
    """Public endpoint to get the auth token for frontend auto-configuration."""
    from lib.security import _is_auth_enabled, _get_expected_token
    if _is_auth_enabled():
        return {"token": _get_expected_token()}
    return {"token": None}

@app.get("/search_naive")
async def search_naive(
    txt_query: str,
    k: int = 10,
    _: None = Depends(require_auth),
    __: None = Depends(require_rate_limit),
):
    try:
        search_results = await rag_base.search_naive(txt_query, chunk_k=k)
        return search_results
    except Exception as e:
        # Log all exceptions with full stack trace before converting to HTTPException
        logger.error("Error in search_naive: %s", e, exc_info=True, extra={"txt_query": txt_query, "k": k})
        # Surface actionable config errors (e.g., missing API keys) to the caller.
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/search")
async def search(
    txt_query: str,
    title_k: int = 3,
    chunk_k: int = 10,
    query_expand_k: int = 1,
    chunk_index: str = None,
    _: None = Depends(require_auth),
    __: None = Depends(require_rate_limit),
):
    if chunk_index is not None:
        title_index = chunk_index + "_titles"
    try:
        search_results, expanded_query = await rag_base.search(
            txt_query, 
            title_k=title_k, 
            chunk_k=chunk_k, 
            query_expand_k=query_expand_k,
            title_index=title_index,
            chunk_index=chunk_index
        )
        return search_results
    except Exception as e:
        # Log all exceptions with full stack trace before converting to HTTPException
        logger.error("Error in search: %s", e, exc_info=True, extra={"txt_query": txt_query, "title_k": title_k, "chunk_k": chunk_k, "query_expand_k": query_expand_k})
        # Surface actionable config errors (e.g., missing API keys) to the caller.
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/chatbot")
async def chatbot(
    txt_query: str,
    query_context: list[str] = Query(default=[]),
    title_k: int = 3,
    chunk_k: int = 10,
    query_expand_k: int = 1,
    chunk_index: str = None,
    _: None = Depends(require_auth),
    __: None = Depends(require_rate_limit),
):
    if chunk_index is not None:
        title_index = chunk_index + "_titles"
    try:
        # Limit query_context to maximum 6 items
        limited_context = query_context[-6:] if len(query_context) > 6 else query_context
        result = await rag_base.chat(
            txt_query, 
            query_context=limited_context,
            title_k=title_k, 
            chunk_k=chunk_k, 
            query_expand_k=query_expand_k,
            title_index=title_index,
            chunk_index=chunk_index
        )
        return result
    except Exception as e:
        # Log all exceptions with full stack trace before converting to HTTPException
        logger.error("Error in chatbot: %s", e, exc_info=True, extra={"txt_query": txt_query, "title_k": title_k, "chunk_k": chunk_k, "query_expand_k": query_expand_k})
        # Surface actionable config errors (e.g., missing API keys) to the caller.
        raise HTTPException(status_code=500, detail=str(e)) from e



# Start server when run directly or in Cloud Functions 2nd gen
# Cloud Functions 2nd gen runs main.py as script, so __name__ == "__main__" will be True
# Check K_SERVICE (Cloud Run sets this) as additional indicator for Cloud Functions 2nd gen
if __name__ == "__main__" or os.environ.get("K_SERVICE"):
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
