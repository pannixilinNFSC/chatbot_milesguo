from lib.agentic.config import AgentState
from lib.llm.rag_prompt import build_rag_prompt
from lib.llm.agentic_prompt import (
    build_prompt_entry, 
    build_prompt_agentic,
    get_entry_response_format, 
    get_agentic_response_format,
)
from lib.llm.litellm_api import call_llm_with_fallback
from lib.search.elastic_mix import ElasticMix
#from lib.agentic.dummy import call_llm_with_fallback, ElasticMix


class Node:
    """
    Node class containing all workflow node functions.
    Each method represents a node in the agentic RAG workflow.
    """
    
    def __init__(self):
        self.elastic_mix = ElasticMix()

    async def entry_llm_node(self, state: AgentState) -> AgentState:
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
        prompt_entry = build_prompt_entry(question, query_context)
        entry_response_format = get_entry_response_format(agentic_config)
        llm_output = await call_llm_with_fallback(prompt_entry, model_name="gpt", response_format=entry_response_format)
        #llm_output = dummy_call_llm_with_fallback(prompt_entry, model_name="gpt", response_format=entry_response_format)
        
        # Extract classification result and handle based on query type
        query_type = llm_output.get("query_type", "not_found")
        if query_type == "need_rag":
            # For RAG queries: empty answer triggers RAG flow, use LLM-generated expanded queries
            answer = ""
            expanded_queries = llm_output["expanded_queries"]
        else:
            # For direct answer types: use LLM-generated answer, keep original question for tracking
            answer = llm_output["answer"]
            expanded_queries = [question]
        
        return {
            **state,
            "query_type": query_type,
            "answer": answer, 
            "expanded_queries": expanded_queries, 
        }

    async def rag_search_node(self, state: AgentState) -> AgentState:
        """
        Second node (non-LLM): Perform RAG search with expanded queries.
        
        This node executes the actual search operation using the expanded queries generated
        in previous nodes. It increments the search_count to track how many search iterations
        have been performed, which is used to prevent infinite loops in the RAG flow.
        
        The search results are stored in state for use by subsequent LLM nodes that generate
        answers or validate the quality of retrieved information.
        """
        search_config = state["search_config"]
        title_index = search_config["title_index"]
        chunk_index = search_config["chunk_index"]
        title_k = search_config["title_k"]
        chunk_k = search_config["chunk_k"]
        
        # Get expanded queries from state, fallback to original question if not available
        expanded_queries = state.get("expanded_queries", [state["question"]])
        search_results = await self.elastic_mix.search(
            expanded_queries, 
            title_index, 
            chunk_index, 
            title_k=title_k, 
            chunk_k=chunk_k, 
        )
        
        # Increment search count to track RAG search iterations
        search_count = state.get("search_count", 0) + 1
        
        return {
            **state,
            "search_results": search_results,
            "search_count": search_count
        }
        
    async def rag_reply_node(self, state: AgentState) -> AgentState:
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
        # Generate answer without structured output to maximize response quality and naturalness
        prompt_rag = build_rag_prompt(question, search_results)
        answer = await call_llm_with_fallback(prompt_rag, model_name="gpt", response_format=None)
        return {**state, "answer": answer}

    async def reply_validation_node(self, state: AgentState) -> AgentState:
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
        historical_queries = state.get("historical_queries", [])
        
        # Check if maximum search iterations have been reached
        exceeded_limit = search_count >= max_search_count
        
        if not exceeded_limit:
            # Use LLM to evaluate answer quality and determine next action
            question = state.get("question", "")
            answer = state.get("answer", "")
            prompt_agentic = build_prompt_agentic(question, answer)
            agentic_response_format = get_agentic_response_format(agentic_config)
            llm_output = await call_llm_with_fallback(prompt_agentic, model_name="gemini", response_format=agentic_response_format)
            
            type_state = llm_output["type_state"]
            refined_queries = llm_output["refined_queries"]
        else:
            type_state = "valid_answer"
            refined_queries = []
            
        if type_state == "valid_answer":
            # Accept current answer: either limit reached or validation passed
            answer = state["answer"]
        else:  # type_state == "refine_query"
            # Refine query for another search iteration
            historical_queries = historical_queries + refined_queries
            answer = ""  # Clear answer to trigger new search and generation
            # Filter search results: keep only those with indices mentioned in answer
            # valid_search_indices contains reference numbers from answer (e.g., "1", "2" from [1][2])
            valid_indices = set(llm_output.get("valid_search_indices", []))
            search_results = [
                result for result in search_results 
                if result["index"] in valid_indices
            ]
        
        return {
            **state,
            "expanded_queries": refined_queries,
            "historical_queries": historical_queries,
            "answer": answer,
            "search_results": search_results,
        }