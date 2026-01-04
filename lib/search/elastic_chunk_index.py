import os
import json
from tqdm import tqdm
from pydantic import BaseModel, Field
from lib.search.elastic_base import ElasticClientBase
from lib.app_logger import get_logger
logger = get_logger(__name__)


class ElasticChunk(BaseModel):
    """Pydantic model for Elasticsearch chunk document structure."""
    doc_id: str
    chunk_id: str
    text: str
    context: str = ""
    doc_summary: str = ""
    doc_title: str = ""
    question: str = ""
    
    def to_elasticsearch_dict(self) -> dict:
        """Convert model to dictionary format for Elasticsearch insertion."""
        doc_dict = self.model_dump()
        doc_dict["_id"] = f"{self.doc_id}_{self.chunk_id}"
        return doc_dict


class ElasticClientChunks(ElasticClientBase):
    def __init__(self, 
                 chunk_index_name="miles_guo", 
                 chunks_path="./data_miles/chunks/",
                 contexts_path="./data_miles/contexts/",
                 title_path="./data_miles/titles.json",
                 summaries_path="./data_miles/summaries.json",
                 ):
        super().__init__(chunk_index_name)
        self.chunks_path = chunks_path
        self.contexts_path = contexts_path
        self.title_path = title_path
        self.summaries_path = summaries_path
        self.existing_ids = self.get_existing_ids()
        
    def get_chunk_id_from_file(self, file: str) -> tuple[str, str]:
        """Extract doc_id and chunk_id from filename.
        """
        basename = os.path.splitext(os.path.basename(file))[0]
        parts = basename.split("_")
        if len(parts) >= 2:
            # chunk_id is the last part, doc_id is everything before it
            chunk_id = parts[-1]
            doc_id = "_".join(parts[:-1])
        else:
            # Fallback for files without underscore (e.g., system.txt)
            doc_id = basename
            chunk_id = "0"
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
        title_txt = self.titles.get(doc_id) or ""
        if not title_txt:
            print(f"Title not found for document {doc_id}")
        
        summary_txt = self.summaries.get(doc_id) or ""
        if not summary_txt:
            print(f"Summary not found for document {doc_id}")
        
        # Ensure we return strings, not None (handle case where dict value is None)
        title_txt = str(title_txt) if title_txt is not None else ""
        summary_txt = str(summary_txt) if summary_txt is not None else ""
        
        return title_txt, summary_txt
    
    def insert_chunks(self, 
                      batch_size = 1000,
                      limit=None, 
                      skip_existing=True
        ):
        with open(self.summaries_path, "r", encoding="utf-8") as f:
            self.summaries = json.load(f)
        with open(self.title_path, "r", encoding="utf-8") as f:
            self.titles = json.load(f)
            
        files = [os.path.join(self.chunks_path, x) for x in os.listdir(self.chunks_path)]
        # Filter out directories and allow text files (.txt, .md, etc.)
        text_extensions = {'.txt', '.md', '.markdown', '.text'}
        files = [f for f in files if os.path.isfile(f) and any(f.lower().endswith(ext) for ext in text_extensions)]
        batch = []
        skipped = 0
        errors = []
        logger.info(f"Inserting {len(files)} chunks")
        if limit is not None:
            files = files[:limit]
            
        for file in tqdm(files, desc="Inserting chunks"):
            try:
                doc_id, chunk_id = self.get_chunk_id_from_file(file)
                _id = f"{doc_id}_{chunk_id}"
                if skip_existing and _id in self.existing_ids:
                    skipped += 1
                    continue
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
                    
                # Create document using Pydantic model
                doc_model = ElasticChunk(
                    doc_id=doc_id,
                    chunk_id=chunk_id,
                    text=chunk_txt,
                    context=context_txt,
                    doc_summary=summary_txt,
                    doc_title=title_txt,
                )
                # Convert to dict for Elasticsearch insertion
                doc = doc_model.to_elasticsearch_dict()
                
                batch.append(doc)
                
                if len(batch) >= batch_size:
                    self.insert_or_update_doc(batch, self.existing_ids)
                    batch = []
                    
            except Exception as e:
                skipped += 1
                errors.append(f"Error processing file {file}: {e}")
                continue
        
        # Insert remaining documents
        if batch:
            try:
                self.insert_or_update_doc(batch, self.existing_ids)
            except Exception as e:
                errors.append(f"Error inserting final batch: {e}")
        
        # Print summary
        if errors:
            print(f"\nSkipped {skipped} files due to errors:")
            for error in errors[:10]:  # Print first 10 errors
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
                
    
    def insert_chunk_single(self, 
                            chunk_txt: str, 
                            doc_id: str="system_doc1", 
                            chunk_id: str=None, 
                            context_txt: str="", 
                            summary_txt: str="", 
                            title_txt: str=""
    ):
        """Insert a single chunk into Elasticsearch.
        """
        if chunk_id is None:
            chunk_ids = self.get_chunk_ids_given_doc_id(doc_id)
            # Filter numeric chunk_ids and convert to int
            numeric_chunk_ids = [int(x) for x in chunk_ids if isinstance(x, str) and x.isdigit()]
            if numeric_chunk_ids:
                # Get the maximum chunk_id and increment by 1
                chunk_id = str(max(numeric_chunk_ids) + 1)
            else:
                # If no existing chunks, start from 0
                chunk_id = "0"
            
        doc_model = ElasticChunk(
            doc_id=doc_id,
            chunk_id=chunk_id,
            text=chunk_txt,
            context=context_txt,
            doc_summary=summary_txt,
            doc_title=title_txt,
        )
        doc = doc_model.to_elasticsearch_dict()
        # Use empty set for existing_ids since we're inserting a single document
        self.insert_or_update_doc([doc], existing_ids=set())
        
                
        
    async def search_chunks_naive(self, 
                            query: str, 
                            k=10, 
                            doc_ids:list[str]=None,
                            index_name=None
        ):
        if index_name is None:
            index_name = self.index_name
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
        
        search_response = await self.async_client.search(
            index=index_name,
            body=query_body,
            size=k
        )
        hits = search_response["hits"]["hits"]
        scores = [hit["_score"] for hit in hits]
        print(f"scores: {scores}")
        results = []
        for hit in hits:
            result = hit["_source"].copy()
            result["score"] = hit["_score"]
            results.append(result)
        return results
        