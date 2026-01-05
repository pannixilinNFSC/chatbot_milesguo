


async def call_llm_with_fallback(prompt, model_name, response_format):
    """
    Dummy LLM call function that returns appropriate format based on response_format.
    
    - If response_format is entry_response_format: returns dict with query_type and either 
      expanded_queries (for need_rag) or answer (for other types)
    - If response_format is agentic_response_format: returns dict with type_state, 
      refined_queries, and invalid_search_indices
    - If response_format is None: returns plain string answer
    """
    # Check response format by comparing the name in json_schema
    if response_format and response_format.get("json_schema", {}).get("name") == "entry_response_format":
        # Entry LLM node: classify query and generate response
        prompt_lower = prompt.lower()
        
        # Classify based on keywords in prompt
        if any(word in prompt_lower for word in ["hello", "hi", "hey", "greetings"]):
            return {
                "query_type": "greeting",
                "answer": "Hello! How can I help you today?"
            }
        elif any(word in prompt_lower for word in ["stupid", "idiot", "dumb", "hate"]):
            return {
                "query_type": "insult",
                "answer": "I'm here to help in a respectful manner. How can I assist you?"
            }
        elif any(word in prompt_lower for word in ["??", "what do you mean", "unclear", "confused"]):
            return {
                "query_type": "unclear",
                "answer": "I'm not sure what you're asking. Could you please clarify your question?"
            }
        else:
            # Default to need_rag for substantive questions
            # Generate expanded queries based on the question
            question = prompt.replace("dummy prompt entry ", "")
            return {
                "query_type": "need_rag",
                "expanded_queries": [question, f"information about {question}"]
            }
    elif response_format and response_format.get("json_schema", {}).get("name") == "agentic_response_format":
        # Validation node: evaluate answer quality
        # For demo purposes, return valid_answer after first iteration
        return {
            "type_state": "valid_answer",
            "refined_queries": [],
            "invalid_search_indices": []
        }
    else:
        # Plain text response (rag_reply_node)
        # Generate answer based on the prompt content
        prompt_lower = prompt.lower()
        if "capital" in prompt_lower and "france" in prompt_lower:
            return "Based on the search results, the capital of France is Paris."
        elif "photosynthesis" in prompt_lower:
            return "Photosynthesis is the process by which plants convert light energy into chemical energy, using carbon dioxide and water to produce glucose and oxygen."
        else:
            return f"Based on the search results: {prompt.replace('dummy prompt answer ', '')}"

class ElasticMix:
    def __init__(self):
        pass

    async def search(self, 
                     query_list, 
                     title_index, 
                     chunk_index, 
                     title_k=3, 
                     chunk_k=10, 
        ) -> list[dict]:
        search_results = []
        for i, query in enumerate(query_list):
            search_results.append({
                "_id": f"result_{i}",
                "content": f"Dummy search result for query: {query}",
                "score": 0.9 - i * 0.1
            })
        return search_results
    


