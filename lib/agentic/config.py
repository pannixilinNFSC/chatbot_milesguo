from typing import TypedDict, List

class SearchConfig(TypedDict):
    title_index: str
    chunk_index: str
    title_k: int
    chunk_k: int
    
class AgenticConfig(TypedDict):
    max_search_count: int

# 1. 定义状态结构
class AgentState(TypedDict):
    question: str # init user query
    query_context: List[str] # query context for RAG search
    answer: str # final answer
    query_type: str  # "greeting", "insult", "unclear", "need_rag"
    historical_queries: List[str] # all queries has been used
    expanded_queries: List[str] # next queries for RAG search
    search_results: List[dict] # search_results for RAG answer
    search_count: int # turns of RAG search
    search_config: SearchConfig # search config
    agentic_config: AgenticConfig # agentic config
    
def get_agent_state_default(
    chunk_index: str = "miles_guo",
    title_k: int = 3,
    chunk_k: int = 10,
    max_search_count: int = 1,
    max_query_expand_k: int = 1,
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
        "historical_queries": [],
        "expanded_queries": [],
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
            "max_search_count": max_search_count,
        }
    }
