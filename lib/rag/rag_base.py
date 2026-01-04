import json
import copy
import textwrap
import asyncio
from lib.search.elastic_2steps import Elastic2Steps
from lib.rag.query_expand import QueryExpander
from lib.rag.prompt import PROMPT_BASE
from lib.llm.litellm_api import call_llm_with_fallback
from lib.app_logger import get_logger

logger = get_logger(__name__)

class RAGBase:
    def __init__(self, title_index="miles_guo_titles", chunk_index="miles_guo"):
        self.title_index = title_index
        self.chunk_index = chunk_index
        self.elastic_2steps = Elastic2Steps(title_index, chunk_index)
        self.prompt_base = PROMPT_BASE
        self.prompt_before = self.prompt_base["prompt1"]
        self.prompt_after = self.prompt_base["prompt2"]
        self.query_expander = QueryExpander()
        self.max_query_expand_k = 3
        self.max_chunk_k = 12
        
    async def search_naive(self, query, chunk_k=10):
        search_results = await self.elastic_2steps.search_naive(query, chunk_k)
        return search_results
        
    async def search_2steps(self, query, title_k=3, chunk_k=10, title_index=None, chunk_index=None):
        search_results = await self.elastic_2steps.search_2steps(query, title_k, chunk_k, title_index=title_index, chunk_index=chunk_index)
        return search_results
    
    async def search(self, query:str, 
                     query_context:list[str]=[], 
                     title_k:int=3, 
                     chunk_k:int=10, 
                     query_expand_k:int=1,
                     expand_query:bool=True,
                     title_index:str=None,
                     chunk_index:str=None
        ) -> tuple[list[dict], list[str]]:
        query_expand_k = min(query_expand_k, self.max_query_expand_k)
        chunk_k = min(chunk_k, self.max_chunk_k)
        
        search_results = []
        query_list = [query]
        expanded_query = []
        if expand_query:
            expanded_query = await self.query_expander.expand(
                query, 
                query_context, 
                k=query_expand_k
            )
            logger.info("Expanded Query: %s", expanded_query)
            query_list += expanded_query
            chunk_k = chunk_k // 2
        
        # Parallelize search operations for all queries
        async def search_per_query(q):
            # Run both search_naive and search_2steps in parallel for each query
            naive_results, steps_results = await asyncio.gather(
                self.search_naive(q, chunk_k=chunk_k),
                self.search_2steps(q, title_k=title_k, chunk_k=chunk_k, title_index=title_index, chunk_index=chunk_index)
            )
            return naive_results + steps_results
        
        # Execute all queries in parallel
        all_results = await asyncio.gather(*[search_per_query(q) for q in query_list])
        # Flatten the results from all queries
        search_results = [item for sublist in all_results for item in sublist]
        logger.info("Total search results: %s", len(search_results))
        
        # reduce cost by deduplicating search results
        search_results = self.deduplicate_search_results(search_results)
        logger.info("Deduplicated search results: %s", len(search_results))
        
        # Add index to each search result
        for index, result in enumerate(search_results, start=1):
            result["index"] = index
        
        return search_results, expanded_query
    
    def deduplicate_search_results(self, search_results: list[dict]) -> list[dict]:
        """
        Remove duplicate field values from search results.
        If a field value appears in a later element that was already seen in an earlier element,
        remove that field from the later element.
        """
        # Track seen values for each field (using JSON serialization for comparison)
        seen_values = {}
        seen_ids = set()
        deduped = []
        
        for result in search_results:
            # Create a copy to avoid modifying the original
            result_copy = copy.deepcopy(result)
            doc_id = result_copy["doc_id"]
            chunk_id = result_copy["chunk_id"]
            unique_id = f"{doc_id}_{chunk_id}"
            if unique_id in seen_ids:
                continue
            seen_ids.add(unique_id)
            
            # Check each field in the result
            for field_name, field_value in list(result_copy.items()):
                # Initialize field tracking if not exists
                if field_name not in seen_values:
                    seen_values[field_name] = set()
                
                # Serialize field value to string for comparison (handles all types)
                try:
                    field_value_str = json.dumps(field_value, sort_keys=True, ensure_ascii=False)
                except (TypeError, ValueError):
                    # If serialization fails, skip this field
                    continue
                
                # If this field value was seen before, remove the field from current result
                if field_value_str in seen_values[field_name]:
                    del result_copy[field_name]
                else:
                    # Record this value for future comparisons
                    seen_values[field_name].add(field_value_str)
            
            deduped.append(result_copy)
        
        return deduped
    
    async def chat(self, query:str, 
                   query_context:list[str]=[], 
                   title_k:int=3, 
                   chunk_k:int=10, 
                   query_expand_k:int=1,
                   expand_query:bool=True,
                   title_index:str=None,
                   chunk_index:str=None
    ) -> tuple[str, list[dict], str]:
        search_results, expanded_query = await self.search(
            query, 
            query_context, 
            title_k=title_k, 
            chunk_k=chunk_k, 
            query_expand_k=query_expand_k,
            expand_query=expand_query,
            title_index=title_index,
            chunk_index=chunk_index
        )
        
        search_results_txt = json.dumps(search_results, ensure_ascii=False)
        
        prompt = f"""{self.prompt_before} 用户本次的话题是：{query} \n"""
        if query_context:
            prompt += f"""这是用户之前的问答记录：{query_context} \n"""
        prompt += f"""以下是参考文本: {search_results_txt} \n"""
        prompt += f"""{self.prompt_after}"""
        
        llm_response = await call_llm_with_fallback(prompt, model_name="gpt")
        
        logger.info("Query Context: %s", "\n".join(query_context))
        logger.info("Query: %s", query)
        logger.info("LLM Response: %s", textwrap.fill(llm_response, width=50))
        logger.info("Search Results: %s", textwrap.fill(search_results_txt, width=50))
        logger.info("LLM Prompt: %s", textwrap.fill(prompt, width=50))
        return llm_response, search_results, prompt