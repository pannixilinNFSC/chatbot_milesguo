import asyncio
import json
import copy
from pydantic import BaseModel

from lib.search.elastic_title_index import ElasticReadClientTitles
from lib.search.elastic_chunk_index import ElasticReadClientChunks
from lib.app_logger import get_logger

logger = get_logger(__name__)

class ElasticMix:
    def __init__(self):
        self.client_title = ElasticReadClientTitles()
        self.client_chunk = ElasticReadClientChunks()
        
    async def search_naive(self, 
                           query, 
                           chunk_index, 
                           chunk_k=10, 
                           doc_ids: list[str]=None):
        """
        Search chunks using multi-match query across text, doc_summary, and context fields.
        """
        chunk_hits = await self.client_chunk.search_chunks_naive(
            query, 
            chunk_index,
            k=chunk_k, 
            doc_ids=doc_ids, 
        )
        return chunk_hits
    
    async def search_neighbour_chunks(self, 
                                      doc_id: str, 
                                      chunk_id: str, 
                                      chunk_index: str, 
                                      distance: int=1, 
                                      **kwargs, 
        )->list[dict]:
        """
        Search neighbouring chunks within specified distance from a given chunk.
        """
        search_results = await self.client_chunk.get_neighbour_chunks(
            chunk_index, doc_id, chunk_id, distance)
        return search_results
        
    async def search_2steps(self, 
                            query: str, 
                            title_index: str, 
                            chunk_index: str, 
                            title_k: int=3, 
                            chunk_k: int=10, 
                            **kwargs, 
        )->list[dict]:
        """
        Two-step search: first find relevant documents by title, then search chunks within those documents.
        """
        title_hits = await self.client_title.search_title_naive(
            query, 
            title_index,
            k=title_k, 
        )
        doc_ids = [hit["doc_id"] for hit in title_hits]
        chunk_hits = await self.client_chunk.search_chunks_naive(
            query, 
            chunk_index,
            k=chunk_k, 
            doc_ids=doc_ids, 
        )
        return chunk_hits
    
    async def search_1step_and_2steps(self, 
                                      query_list: list[str], 
                                      title_index: str, 
                                      chunk_index: str, 
                                      title_k: int=3, 
                                      chunk_k: int=10, 
                                      **kwargs, 
        )->list[dict]:
        """
        Search using both 1-step and 2-step approaches.
        """
        tasks = []
        tasks += [self.search_naive(query, chunk_index, chunk_k=chunk_k) 
            for query in query_list]
        tasks += [self.search_2steps(query, title_index, chunk_index, title_k=title_k, chunk_k=chunk_k)
            for query in query_list]
        results_list = await asyncio.gather(*tasks)
        results = [item for sublist in results_list for item in sublist]
        return results
    
    async def search_ops(self, 
                         ops: list[dict], 
                         title_index: str, 
                         chunk_index: str, 
                         title_k: int=3, 
                         chunk_k: int=10, 
        )->list[dict]:
        """
        Search using a list of operations.
        """
        ops_func_mapping = {
            "search_general": self.search_1step_and_2steps, 
            "search_doc": self.search_naive, 
            "search_neighbour_chunks": self.search_neighbour_chunks,
        }
        kwargs_default = {
            "title_index": title_index,
            "chunk_index": chunk_index,
            "title_k": title_k,
            "chunk_k": chunk_k,
        }
        
        tasks = []
        for op in ops:
            type1 = op["type"]
            kwargs1 = kwargs_default.copy()
            kwargs1.update(op)
            
            func1 = ops_func_mapping[type1]
            tasks += [func1(**kwargs1)]
        
        results_list = await asyncio.gather(*tasks)
        search_results = [item for sublist in results_list for item in sublist]
        search_results = self.postprocess_search_results(search_results)
        return search_results
    
    async def search(self, 
                     query_list, 
                     title_index, 
                     chunk_index, 
                     title_k=3, 
                     chunk_k=10, 
        ) -> list[dict]:
        
        ops = [
            {
                "type": "search_general",
                "query_list": query_list,
            }
        ]
        
        search_results = await self.search_ops(
            ops, title_index, chunk_index, title_k=title_k, chunk_k=chunk_k)
        
        return search_results
    
    def postprocess_search_results(self, search_results: list[dict]) -> list[dict]:
        """
        Remove duplicate field values from search results.
        If a field value appears in a later element that was already seen in an earlier element,
        remove that field from the later element.
        
        Critical fields needed for display (doc_id, chunk_id, doc_title, index, score) are never removed.
        """
        # Fields that must always be preserved for frontend display
        PRESERVE_FIELDS = {"doc_id", "chunk_id", "doc_title", "index", "score", "_score"}
        
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
                # Never remove critical display fields
                if field_name in PRESERVE_FIELDS:
                    continue
                    
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
            
        logger.info("Deduplicated search results: %s", len(deduped))
        
        # Add index to each search result
        for index, result in enumerate(deduped, start=1):
            result["index"] = index
        
        return deduped