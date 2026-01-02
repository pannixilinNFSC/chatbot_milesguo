import os
import json
from tqdm import tqdm
from lib.search.elastic_base import ElasticClientBase



class ElasticClientMilesChunks(ElasticClientBase):
    def __init__(self, 
                 chunk_index_name="miles_guo", 
                 chunks_path="./data/chunks/",
                 contexts_path="./data/contexts/",
                 title_path="./data/titles.json",
                 summaries_path="./data/summaries.json",
                 ):
        super().__init__(chunk_index_name)
        self.chunks_path = chunks_path
        self.contexts_path = contexts_path
        self.title_path = title_path
        self.summaries_path = summaries_path
        with open(self.summaries_path, "r", encoding="utf-8") as f:
            self.summaries = json.load(f)
        with open(self.title_path, "r", encoding="utf-8") as f:
            self.titles = json.load(f)
        
    def get_chunk_id_from_file(self, file: str) -> str:
        basename = os.path.splitext(os.path.basename(file))[0]
        doc_id, chunk_id = basename.split("_")[:2]
        return doc_id, chunk_id
    
    def _read_chunk_file(self, file: str) -> str:
        """Read chunk text from file."""
        with open(file, "r", encoding="utf-8") as f:
            return f.read()
    
    def _read_context_file(self, doc_id: str, chunk_id: str) -> str:
        """Read context text from file, returns empty string if not found."""
        context_file = os.path.join(self.contexts_path, f"{doc_id}_{chunk_id}.txt")
        try:
            with open(context_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""
    
    def _get_document_metadata(self, doc_id: str) -> tuple[str, str]:
        """Get title and summary for a document, returns empty strings if not found."""
        title_txt = self.titles.get(doc_id, "")
        if not title_txt:
            print(f"Title not found for document {doc_id}")
        
        summary_txt = self.summaries.get(doc_id, "")
        if not summary_txt:
            print(f"Summary not found for document {doc_id}")
        
        return title_txt, summary_txt
    
    def insert_chunks(self, 
                      batch_size = 1000,
                      limit=None, 
                      skip_existing=True
        ):
        existing_ids = set()
        if skip_existing:
            existing_ids = self.get_existing_ids()
            
        files = [os.path.join(self.chunks_path, x) for x in os.listdir(self.chunks_path)]
        # Filter out directories and non-txt files
        files = [f for f in files if os.path.isfile(f) and f.endswith('.txt')]
        batch = []
        skipped = 0
        errors = []
        if limit is not None:
            files = files[:limit]
            
        for file in tqdm(files, desc="Inserting chunks"):
            try:
                doc_id, chunk_id = self.get_chunk_id_from_file(file)
                
                # Read chunk file
                try:
                    chunk_txt = self._read_chunk_file(file)
                except Exception as e:
                    skipped += 1
                    errors.append(f"Error reading chunk file {file}: {e}")
                    continue
                
                # Read context file
                context_txt = self._read_context_file(doc_id, chunk_id)
                
                # Get document metadata
                title_txt, summary_txt = self._get_document_metadata(doc_id)
                question_txt = ""
                    
                doc = {
                    "_id": f"{doc_id}_{chunk_id}",
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "text": chunk_txt,
                    "context": context_txt,
                    "doc_summary": summary_txt, 
                    "doc_title": title_txt,
                    "question": question_txt
                }
                
                batch.append(doc)
                
                if len(batch) >= batch_size:
                    self.insert_or_update_doc(batch, existing_ids)
                    batch = []
                    
            except Exception as e:
                skipped += 1
                errors.append(f"Error processing file {file}: {e}")
                continue
        
        # Insert remaining documents
        if batch:
            try:
                self.insert_or_update_doc(batch, existing_ids)
            except Exception as e:
                errors.append(f"Error inserting final batch: {e}")
        
        # Print summary
        if errors:
            print(f"\nSkipped {skipped} files due to errors:")
            for error in errors[:10]:  # Print first 10 errors
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
        
    def search_chunks_naive(self, 
                            query: str, 
                            k=10, 
                            doc_ids:list[str]=None
        ):
        multi_match_query = {
            "multi_match": {
                "query": query,
                "fields": [
                    "text^2",
                    "doc_summary",
                    "context"
                ]
            }
        }
        
        if doc_ids is not None:
            query_body = {
                "query": {
                    "bool": {
                        "must": [multi_match_query],
                        "filter": [
                            {
                                "terms": {
                                    "doc_id": doc_ids
                                }
                            }
                        ]
                    }
                }
            }
        else:
            query_body = {
                "query": multi_match_query
            }
        
        search_response = self.client.search(
            index=self.index_name,
            body=query_body,
            size=k
        )
        hits = search_response["hits"]["hits"]
        hits = [hit["_source"] for hit in hits]
        return hits
        