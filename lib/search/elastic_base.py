from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv
import os


class ElasticClientBase:
    def __init__(self, index_name):
        """
        Initialize Elasticsearch client with optimized settings for faster startup.
        
        Args:
            index_name: Name of the Elasticsearch index
            connect_timeout: Connection timeout in seconds (default: 2, set lower for faster startup)
            max_retries: Maximum retries for connection (default: 0 to fail fast)
        """
        load_dotenv()
        ELASTIC_API_KEY = os.getenv("ELASTIC_API_KEY")
        ELASTIC_URL = os.getenv("ELASTIC_URL")
        self.client = Elasticsearch(
            ELASTIC_URL,
            api_key=ELASTIC_API_KEY, 
            verify_certs=False,
            ssl_show_warn=False,
            request_timeout=10,
        )
        self.index_name = index_name
        
    def clear_index(self):
        self.client.indices.delete(index=self.index_name)
        self.client.indices.create(index=self.index_name)
        self.update_mappings()
        print(f"Index {self.index_name} cleared and mappings updated")
        return True

    def update_mappings(self, mappings=None):
        if mappings is None:
            mappings = {
                "properties": {
                    "chunk_id": {
                        "type": "keyword"
                    },
                    "doc_id": {
                        "type": "keyword"
                    },
                    "text": {
                        "type": "text"
                    },
                    "context": {
                        "type": "text"
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
    
    
    def get_existing_ids(self, batch_size=1000):
        """
        Get all document IDs that exist in Elasticsearch index.
        
        Args:
            batch_size: Number of documents to retrieve per batch (for scroll API)
            
        Returns:
            set: Set of all document IDs in the index
        """
        all_ids = set()
        
        print(f"Retrieving all document IDs from index {self.index_name}...")
        try:
            # Use scroll API to get all document IDs
            response = self.client.search(
                index=self.index_name,
                body={
                    "query": {"match_all": {}},
                    "_source": False  # Only return _id, not the document content
                },
                size=batch_size,
                scroll='2m'
            )
            
            scroll_id = response.get('_scroll_id')
            hits = response['hits']['hits']
            
            while hits:
                for hit in hits:
                    all_ids.add(hit['_id'])
                
                if scroll_id:
                    response = self.client.scroll(
                        scroll_id=scroll_id,
                        scroll='2m'
                    )
                    hits = response['hits']['hits']
                    scroll_id = response.get('_scroll_id')
                else:
                    break
            
            # Clear scroll context
            if scroll_id:
                self.client.clear_scroll(scroll_id=scroll_id)
                
        except Exception as e:
            print(f"Error retrieving document IDs: {e}")
        
        if all_ids:
            print(f"Found {len(all_ids)} documents in index")
        
        return all_ids

    def insert_doc(self, docs):
        bulk_response = helpers.bulk(
            self.client, 
            docs, 
            index=self.index_name)
        return bulk_response
    
    def insert_or_update_doc(self, docs, existing_ids):
        """
        Insert or update documents based on existing_ids. Uses bulk operations for better performance.
        
        Args:
            docs: List of documents to insert/update, each should have "_id" field
            existing_ids: Set of document IDs that already exist in the index
            
        Returns:
            tuple: (success_count, failed_count) from bulk operation
        """
        bulk_actions = []
        for doc in docs:
            doc_id = doc.get("_id")
            if doc_id is None:
                continue
            
            # Create a copy without _id for the document body
            doc_body = {k: v for k, v in doc.items() if k != "_id"}
            
            if doc_id in existing_ids:
                # Update existing document
                bulk_actions.append({
                    "_op_type": "update",
                    "_id": doc_id,
                    "doc": doc_body,
                    "doc_as_upsert": False  # Only update, don't create if missing
                })
            else:
                # Insert new document
                bulk_actions.append({
                    "_op_type": "index",
                    "_id": doc_id,
                    "_source": doc_body
                })
        
        if not bulk_actions:
            return (0, 0)
        
        try:
            bulk_response = helpers.bulk(
                self.client,
                bulk_actions,
                index=self.index_name
            )
            return bulk_response
        except Exception as e:
            print(f"Error in bulk insert/update: {e}")
            return (0, len(bulk_actions))
    
    def search_doc(self, query, k=10):
        search_response = self.client.search(
            index=self.index_name,
            body={
                "query": {
                    "match": {
                        "text": query
                    }
                }
            }
        )
        return search_response