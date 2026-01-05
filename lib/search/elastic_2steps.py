from lib.search.elastic_title_index import ElasticReadClientTitles
from lib.search.elastic_chunk_index import ElasticReadClientChunks

class Elastic2Steps:
    def __init__(self):
        self.client_title = ElasticReadClientTitles()
        self.client_chunk = ElasticReadClientChunks()
        
    async def search_naive(self, 
                           query:str, 
                           index_name:str,
                           k:int=10, 
                           ):
        chunk_hits = await self.client_chunk.search_chunks_naive(
            query, 
            index_name,
            k=k, 
        )
        return chunk_hits
        
    async def search_2steps(self, 
                            query:str, 
                            title_index:str,
                            chunk_index:str,
                            title_k:int=10, 
                            chunk_k:int=10,
                            ):
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