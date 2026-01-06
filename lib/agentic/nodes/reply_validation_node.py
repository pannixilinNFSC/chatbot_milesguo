from lib.agentic.config import AgentState
from lib.agentic.prompts import get_agentic_prompt_and_format
from lib.llm.litellm_api import call_llm_with_fallback


async def reply_validation_node(state: AgentState) -> AgentState:
    """
    Fourth node (third LLM node): Validate answer quality and refine queries if needed.
    
    This node evaluates whether the generated answer adequately addresses the user's query.
    It uses structured output to determine one of two states:
    - "valid_answer": The current answer is sufficient, workflow can proceed to final answer
    - "refine_query": The answer needs improvement, generate refined queries for another search iteration
    
    The node also enforces a maximum search count limit to prevent infinite loops. If the limit
    is exceeded, it accepts the current answer regardless of validation result.
    
    When refining queries, it filters out invalid search results based on LLM feedback and
    updates historical queries to track all search attempts.
    """
    agentic_config = state.get("agentic_config", {})
    max_search_count = agentic_config.get("max_search_count", 3)
    search_count = state.get("search_count", 0)
    search_results = state.get("search_results", [])
    
    # Check if maximum search iterations have been reached
    exceeded_limit = search_count >= max_search_count
    
    if not exceeded_limit:
        # Use LLM to evaluate answer quality and determine next action
        question = state.get("question", "")
        answer = state.get("answer", "")
        search_results = state.get("search_results", [])
        prompt_agentic, agentic_response_format = get_agentic_prompt_and_format(question, answer, search_results, agentic_config)
        llm_output = await call_llm_with_fallback(
            prompt_agentic, 
            model_name="gemini", 
            response_format=agentic_response_format
        )
        
        type_state = llm_output["type_state"]
        search_ops = llm_output["search_ops"]
    else:
        type_state = "valid_answer"
        search_ops = None
        
    if type_state == "valid_answer":
        # Accept current answer: either limit reached or validation passed
        answer = state["answer"]
    else:  # type_state == "refine_query"
        # Refine query for another search iteration
        answer = ""  # Clear answer to trigger new search and generation
        
    
    return {
        **state,
        "search_ops": search_ops,
        "answer": answer,
        "search_results": search_results,
    }

