import os
import json
import re
import asyncio
from tqdm import tqdm

from lib.llm.litellm_api import call_llm_with_fallback

class SummaryExtractor:
    """Extract and manage document summaries from text files"""
    
    def __init__(self, 
                 input_dir="./data_miles/documents/", 
                 output_file="./data_miles/summaries.json",
                 max_workers=8,
                 limit=None):
        """
        Initialize SummaryExtractor
        
        Args:
            input_dir: Directory containing text files to extract summaries from
            output_file: Output file path for extracted summaries
            max_workers: Maximum number of parallel tasks
        """
        self.input_dir = input_dir
        self.output_file = output_file
        self.max_workers = max_workers
        self.limit = limit
    
    async def _process_file(self, in_file, semaphore, pbar):
        """Process a single file to extract summary"""
        async with semaphore:
            try:
                id = os.path.basename(in_file).split(".")[0]
                with open(in_file, "r", encoding="utf-8") as f:
                    txt = f.read()
                summary = await self.get_summary(txt)
                return id, summary
            finally:
                pbar.update(1)

    async def run(self, skip_existing=True):
        """
        Extract summary of each document and organize by ID into a JSON file using async parallel processing
        Skips documents that already exist in the output file
        """
        # Load existing summaries if output file exists
        existing_summaries = {}
        if skip_existing and os.path.exists(self.output_file):
            with open(self.output_file, "r", encoding="utf-8") as f:
                existing_summaries = json.load(f)
        
        # Get all files and filter out already processed ones
        all_files = [os.path.join(self.input_dir, x) for x in os.listdir(self.input_dir)]
        files = []
        for in_file in all_files:
            doc_id = os.path.basename(in_file).split(".")[0]
            if doc_id not in existing_summaries:
                files.append(in_file)
        
        if self.limit is not None:
            files = files[:self.limit]
        
        if not files:
            print("All documents have already been processed.")
            return
        
        semaphore = asyncio.Semaphore(self.max_workers)
        
        with tqdm(total=len(files), desc="Extracting summaries") as pbar:
            tasks = [self._process_file(in_file, semaphore, pbar) for in_file in files]
            results = await asyncio.gather(*tasks)
        
        # Merge new results with existing summaries
        new_summaries = {id: summary for id, summary in results}
        existing_summaries.update(new_summaries)
        
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(existing_summaries, f, indent=2, ensure_ascii=False)
    
    async def get_summary(self, txt: str):
        prompt = f"请对以下演讲的核心内容进行摘要，突出核心命名实体名称，不超过100个字。以下是文本：{txt}"
        summary = await call_llm_with_fallback(prompt)
        return summary