import asyncio
import json
import copy
from lib.search.elastic_2steps import Elastic2Steps
from lib.app_logger import get_logger
logger = get_logger(__name__)


class ElasticMix:
    def __init__(self):
        self.elastic_2steps = Elastic2Steps()
        
    async def search_naive(self, query, chunk_index, chunk_k=10):
        search_results = await self.elastic_2steps.search_naive(query, chunk_index, k=chunk_k)
        return search_results
        
    async def search_2steps(self, query, title_index, chunk_index, title_k=3, chunk_k=10):
        search_results = await self.elastic_2steps.search_2steps(query, title_index, chunk_index, title_k=title_k, chunk_k=chunk_k)
        return search_results
        
    async def search(self, 
                     query_list, 
                     title_index, 
                     chunk_index, 
                     title_k=3, 
                     chunk_k=10, 
        ) -> list[dict]:
        search_results = []
        # Parallelize search operations for all queries
        async def search_per_query(q):
            # Run both search_naive and search_2steps in parallel for each query
            naive_results, steps_results = await asyncio.gather(
                self.search_naive(q, chunk_index, chunk_k=chunk_k),
                self.search_2steps(q, title_index, chunk_index, title_k=title_k, chunk_k=chunk_k)
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
        
        return search_results
    
    def deduplicate_search_results(self, search_results: list[dict]) -> list[dict]:
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
        
        return deduped