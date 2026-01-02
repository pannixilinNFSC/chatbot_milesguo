import os
import json
from pydantic_core.core_schema import NoneSchema
from tqdm import tqdm
from lib.search.elastic_base import ElasticClientBase


class ElasticClientMilesTitles(ElasticClientBase):
    def __init__(self, 
                 title_index_name="miles_guo_titles",
                 title_path="./data/titles.json",
                 summaries_path="./data/summaries.json",
                 ):
        super().__init__(title_index_name)
        self.title_path = title_path
        self.summaries_path = summaries_path
        with open(self.summaries_path, "r", encoding="utf-8") as f:
            self.summaries = json.load(f)
        with open(self.title_path, "r", encoding="utf-8") as f:
            self.titles = json.load(f)
            
    def clear_index(self):
        self.client.indices.delete(index=self.index_name)
        self.client.indices.create(index=self.index_name)
        self.update_mappings()
        return True
    
    def update_mappings(self, mappings=None):
        if mappings is None:
            mappings = {
                "properties": {
                    "doc_id": {
                        "type": "keyword"
                    },
                    "doc_summary": {
                        "type": "text"
                    },
                    "doc_title": {
                        "type": "text"
                    },
                    "question1": {
                        "type": "text"
                    }
                }
            }
        mapping_response = self.client.indices.put_mapping(
            index=self.index_name, 
            body=mappings
        )
        return mapping_response
    
        
    def insert_titles(self, limit=None, skip_existing=True):
        # Check which documents already exist
        existing_ids = set()
        if skip_existing:
            existing_ids = self.get_existing_ids()
        
        batch_size = 100
        batch = []
        processed = 0
        skipped = 0
        for doc_id, title in self.titles.items():
            if limit and processed >= limit:
                break
            if skip_existing and doc_id in existing_ids:
                skipped += 1
                continue
            
            summary = self.summaries.get(doc_id, None)
            if not summary:
                print(f"Summary not found for document {doc_id}")
                summary = ""
            question = ""
            doc = {
                "_id": doc_id,
                "doc_id": doc_id,
                "doc_summary": summary,
                "doc_title": title,
                "question1": question
            }
            batch.append(doc)
            processed += 1
            if len(batch) >= batch_size:
                self.insert_doc(batch)
                batch = []
        if batch:
            self.insert_doc(batch)
        
        print(f"Inserted {processed} documents, skipped {skipped} existing documents")
        
    async def search_title_naive(self, query, k=10):
        """
        Search titles by query, sorted by relevance score (default).
        
        Args:
            query: Search query string
            k: Number of results to return (default: 10)
            
        Returns:
            list: List of document sources, sorted by relevance score (descending)
        """
        query_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "doc_summary^2",
                        "doc_title"
                    ]
                }
            },
            "size": k,
            "sort": ["_score"]  # Explicitly sort by score (descending is default)
        }
        search_response = await self.async_client.search(
            index=self.index_name,
            body=query_body
        )
        hits = search_response["hits"]["hits"]
        hits = [hit["_source"] for hit in hits]
        return hits
        
        