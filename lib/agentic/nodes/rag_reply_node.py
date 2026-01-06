from lib.agentic.config import AgentState
from lib.agentic.prompts import get_rag_prompt_and_format
from lib.llm.litellm_api import call_llm_with_fallback


async def rag_reply_node(state: AgentState) -> AgentState:
    """
    Third node (second LLM node): Generate answer based on RAG search results.
    
    This node uses the search results from rag_search_node to generate a comprehensive
    answer to the user's query. It does not use structured output format to allow the
    LLM maximum flexibility in generating natural, high-quality responses.
    
    The generated answer is stored in state and may be validated in subsequent nodes
    to ensure it adequately addresses the user's question.
    """
    question = state.get("question", "")
    search_results = state.get("search_results", [])
    agentic_config = state.get("agentic_config", {})
    # Generate answer without structured output to maximize response quality and naturalness
    prompt_rag, rag_response_format = get_rag_prompt_and_format(question, search_results, agentic_config)
    llm_output = await call_llm_with_fallback(prompt_rag, model_name="gpt", response_format=rag_response_format)
    answer = llm_output["answer"]
    # Filter search results: keep only those with indices mentioned in answer
    # valid_search_indices contains reference numbers from answer (e.g., "1", "2" from [1][2])
    valid_indices = set(llm_output.get("valid_search_indices", []))
    search_results = [
        result for result in search_results 
        if result["index"] in valid_indices
    ]
    return {**state, 
            "answer": answer,
            "search_results": search_results,
            }

