import json
from lib.search.elastic_2steps import Elastic2Steps
from lib.llm.litellm_api import call_llm_with_fallback

class RAGBase:
    def __init__(self, title_index="miles_guo_titles", chunk_index="miles_guo"):
        self.elastic_2steps = Elastic2Steps(title_index, chunk_index)
        with open("prompt.json", "r") as f:
            self.prompt_base = json.load(f)
        self.prompt_before = self.prompt_base["prompt1"]
        self.prompt_after = self.prompt_base["prompt2"]
        
    def search(self, query, k=10):
        search_results = self.elastic_2steps.search_2steps(query, k)
        return search_results
    
    async def chat(self, query, k=10):
        search_results = self.search(query, k)
        #prompt = "You are an assistant for question-answering tasks. 用中文回答问题。"
        search_results_txt = json.dumps(search_results, ensure_ascii=False)
        
        prompt = f"""
{self.prompt_before} {query}
"以下是参考文本
{search_results_txt}
{self.prompt_after}
        """
        
        content = await call_llm_with_fallback(prompt, model_name="gpt")
        return content, search_results, prompt