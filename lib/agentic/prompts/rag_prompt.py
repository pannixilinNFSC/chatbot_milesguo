from lib.rag.rag_prompt import build_rag_prompt


def get_rag_prompt_and_format(question, search_results, agentic_config=None):
    """
    Build RAG prompt and response format together.
    
    Returns:
        tuple: (prompt, response_format)
    """
    rag_prompt = build_rag_prompt(question, search_results)
    rag_prompt += ""
    
    rag_schema = {
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
            },
            "valid_search_indices": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "List of search index values that are mentioned in the answer"
            },
        },
        "required": ["answer", "valid_search_indices"]
    }
    rag_response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "rag_response_format",
            "schema": dict(rag_schema)
        }
    }
    
    return rag_prompt, rag_response_format

