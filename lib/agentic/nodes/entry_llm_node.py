from lib.agentic.config import AgentState
from lib.agentic.prompts import get_entry_prompt_and_format
from lib.llm.litellm_api import call_llm_with_fallback


async def entry_llm_node(state: AgentState) -> AgentState:
    """
    First LLM node: Classify the input type and generate direct answer if needed.
    
    This node uses LLM with structured output to classify user queries into four categories:
    - "greeting": Casual conversation or greetings, returns friendly response directly
    - "insult": Inappropriate language, returns professional response directly
    - "unclear": Vague or ambiguous questions, returns clarification request directly
    - "need_rag": Clear substantive questions requiring information retrieval, triggers RAG flow
    
    For "need_rag" type, the node also generates initial expanded queries for RAG search.
    For other types, it generates direct answers and uses original question as expanded_queries.
    """
    question = state["question"]
    query_context = state.get("query_context", [])
    agentic_config = state.get("agentic_config", {})
    
    # Call LLM with structured output format to get classification and response
    prompt_entry, entry_response_format = get_entry_prompt_and_format(question, query_context, agentic_config)
    llm_output = await call_llm_with_fallback(prompt_entry, model_name="gpt", response_format=entry_response_format)
    #llm_output = dummy_call_llm_with_fallback(prompt_entry, model_name="gpt", response_format=entry_response_format)
    
    # Extract classification result and handle based on query type
    query_type = llm_output.get("query_type", "not_found")
    if query_type == "need_rag":
        # For RAG queries: empty answer triggers RAG flow, use LLM-generated expanded queries
        answer = ""
        expanded_queries = [question] + llm_output["expanded_queries"]
        search_ops = [{"type": "search_general", "query_list": expanded_queries}]
    else:
        # For direct answer types: use LLM-generated answer, keep original question for tracking
        answer = llm_output["answer"]
        search_ops = None
    
    return {
        **state,
        "query_type": query_type,
        "answer": answer, 
        "search_ops": search_ops, 
    }

