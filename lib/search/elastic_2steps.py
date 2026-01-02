from lib.search.elastic_title_index import ElasticClientTitles
from lib.search.elastic_chunk_index import ElasticClientChunks

class Elastic2Steps:
    def __init__(self, 
                 title_index="miles_guo_titles",
                 chunk_index="miles_guo",
                 ):
        self.title_index = title_index
        self.chunk_index = chunk_index
        self.client_title = ElasticClientTitles(title_index)
        self.client_chunk = ElasticClientChunks(chunk_index)
        
    async def search_naive(self, query, chunk_k=10):
        chunk_hits = await self.client_chunk.search_chunks_naive(query, chunk_k)
        return chunk_hits
        
    async def search_2steps(self, query, title_k=10, chunk_k=10):
        title_hits = await self.client_title.search_title_naive(query, title_k)
        doc_ids = [hit["doc_id"] for hit in title_hits]
        chunk_hits = await self.client_chunk.search_chunks_naive(query, chunk_k, doc_ids=doc_ids)
        return chunk_hits