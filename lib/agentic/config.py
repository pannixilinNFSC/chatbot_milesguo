from typing import TypedDict, List

class SearchConfig(TypedDict):
    title_index: str
    chunk_index: str
    title_k: int
    chunk_k: int
    
class AgenticConfig(TypedDict):
    max_iter: int
    max_query_expand_k: int

# 1. 定义状态结构
class AgentState(TypedDict, total=False):
    question: str # init user query
    query_context: List[str] # query context for RAG search
    answer: str # final answer
    query_type: str  # "greeting", "insult", "unclear", "need_rag"
    historical_search_ops: List[str] # all search ops has been used
    search_ops: List[str] # next search ops for RAG search
    search_results: List[dict] # search_results for RAG answer
    search_count: int # turns of RAG search
    search_config: SearchConfig # search config
    agentic_config: AgenticConfig # agentic config
    enable_streaming: bool # enable streaming output in rag_reply_node
    
def get_agent_state_default(
    chunk_index: str = "miles_guo",
    title_k: int = 3,
    chunk_k: int = 12,
    max_iter: int = 2,
    max_query_expand_k: int = 2,
    ):
    """
    Get default AgentState dictionary with all fields initialized.
    TypedDict cannot be instantiated like a class, so we return a plain dict.
    """
    title_index = f"{chunk_index}_titles"
    return {
        "question": "",
        "query_context": [],
        "answer": "",
        "query_type": "",
        "historical_search_ops": [],
        "search_ops": [],
        "search_results": [],
        "search_count": 0,
        "search_config": {
            "title_index": title_index,
            "chunk_index": chunk_index,
            "title_k": title_k,
            "chunk_k": chunk_k,
        }, 
        "agentic_config": {
            "max_query_expand_k": max_query_expand_k,
            "max_iter": max_iter,
        }
    }
