import json
import copy
import textwrap
import asyncio
#from lib.search.elastic_2steps import Elastic2Steps
from lib.search.elastic_mix import ElasticMix
from lib.rag.query_expand import QueryExpander
from lib.rag.prompt import PROMPT_BASE
from lib.llm.litellm_api import call_llm_with_fallback
from lib.app_logger import get_logger

logger = get_logger(__name__)

class RAGBase:
    def __init__(self):
        self.elastic_mix = ElasticMix()
        self.prompt_base = PROMPT_BASE
        self.prompt_before = self.prompt_base["prompt1"]
        self.prompt_after = self.prompt_base["prompt2"]
        self.query_expander = QueryExpander()
        self.max_query_expand_k = 3
        self.max_chunk_k = 12
        
    
    async def search(self, query:str, 
                     title_index:str,
                     chunk_index:str,
                     query_context:list[str]=[], 
                     title_k:int=3, 
                     chunk_k:int=10, 
                     query_expand_k:int=0,
        ) -> tuple[list[dict], list[str]]:
        query_expand_k = min(query_expand_k, self.max_query_expand_k)
        chunk_k = min(chunk_k, self.max_chunk_k)
        
        search_results = []
        query_list = [query]
        expanded_query = []
        if query_expand_k > 0:
            expanded_query = await self.query_expander.expand(
                query, 
                query_context, 
                k=query_expand_k
            )
            logger.info("Expanded Query: %s", expanded_query)
            query_list += expanded_query
            chunk_k = chunk_k // 2
        
        search_results = await self.elastic_mix.search(
            query_list, 
            title_index, 
            chunk_index, 
            title_k=title_k, 
            chunk_k=chunk_k
        )
        
        # Add index to each search result
        for index, result in enumerate(search_results, start=1):
            result["index"] = index
        
        return search_results, expanded_query
    
    
    async def chat(self, query:str, 
                   title_index:str,
                   chunk_index:str,
                   query_context:list[str]=[], 
                   title_k:int=3, 
                   chunk_k:int=10, 
                   query_expand_k:int=1,
                   prompt_before:str=None,
                   prompt_after:str=None
    ) -> tuple[str, list[dict], str]:
        # step 1: search
        search_results, expanded_queries = await self.search(
            query, 
            title_index,
            chunk_index,
            query_context, 
            title_k=title_k, 
            chunk_k=chunk_k, 
            query_expand_k=query_expand_k,
        )
        
        # step 2: generate prompt
        search_results_txt = json.dumps(search_results, ensure_ascii=False)
        
        if not prompt_before:
            prompt_before = self.prompt_before
        if not prompt_after:
            prompt_after = self.prompt_after
        
        prompt = f"""{prompt_before} 用户本次的话题是：{query} \n"""
        if query_context:
            prompt += f"""这是用户之前的问答记录：{query_context} \n"""
        prompt += f"""以下是参考文本: {search_results_txt} \n"""
        prompt += f"""{prompt_after}"""
        
        # step 3: call LLM
        llm_response = await call_llm_with_fallback(prompt, model_name="gpt")
        
        logger.info("Query Context: %s", "\n".join(query_context))
        logger.info("Query: %s", query)
        logger.info("LLM Response: %s", textwrap.fill(llm_response, width=50))
        logger.info("Search Results: %s", textwrap.fill(search_results_txt, width=50))
        logger.info("LLM Prompt: %s", textwrap.fill(prompt, width=50))
        
        result = {
            "content": llm_response,
            "search_results": search_results,
            "prompt": prompt, 
            "querys": [query] + expanded_queries,
        }
        return result