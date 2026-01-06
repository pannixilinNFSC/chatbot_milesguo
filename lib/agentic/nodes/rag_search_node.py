from lib.agentic.config import AgentState
from lib.search.elastic_mix import ElasticMix


async def rag_search_node(state: AgentState, elastic_mix: ElasticMix) -> AgentState:
    """
    Second node (non-LLM): Perform RAG search with expanded queries.
    
    This node executes the actual search operation using the expanded queries generated
    in previous nodes. It increments the search_count to track how many search iterations
    have been performed, which is used to prevent infinite loops in the RAG flow.
    
    The search results are stored in state for use by subsequent LLM nodes that generate
    answers or validate the quality of retrieved information.
    """
    search_config = state["search_config"]
    search_ops = state["search_ops"]
    historical_search_ops = state["historical_search_ops"]
    if search_ops is None:
        search_ops = [{"type": "search_general", "query_list": [state["question"]]}]
    historical_search_ops = historical_search_ops + search_ops
    title_index = search_config["title_index"]
    chunk_index = search_config["chunk_index"]
    title_k = search_config["title_k"]
    chunk_k = search_config["chunk_k"]
    
    search_results = await elastic_mix.search_ops(
        search_ops, 
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
        "search_count": search_count,
        "historical_search_ops": historical_search_ops,
    }

