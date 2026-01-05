from typing import TypedDict, List

# 1. 定义状态结构
class AgentState(TypedDict):
    question: str # init user query
    answer: str # final answer
    query_type: str  # "greeting", "insult", "unclear", "need_rag"
    historical_queries: List[str] # all queries has been used
    expanded_queries: List[str] # next queries for RAG search
    search_results: List[dict] # search_results for RAG answer
    search_count: int # turns of RAG search


def build_prompt_entry(question):
    return f"dummy prompt entry {question}"

def build_prompt_answer(search_results):
    return f"dummy prompt answer {search_results}"

def build_prompt_agentic(answer):
    return f"dummy prompt agentic {answer}"

entry_schema = "dummy entry_schema"
entry_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "entry_response_format",
        "schema": entry_schema
    }
}
agentic_schema = "dummy agentic_schema"
agentic_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "agentic_response_format",
        "schema": agentic_schema
    }
}