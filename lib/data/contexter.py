import os
import json
import asyncio
from tqdm import tqdm
from lib.llm.litellm_api import call_llm_with_fallback

class ContextGenerator:
    def __init__(self, 
                 chunks_folder="./data_miles/chunks/", 
                 summaries_path="./data_miles/summaries.json",
                 output_folder="./data_miles/contexts/", 
                 limit=None,
                 skip_existing=True,
                 context_step=2
            ):
        self.chunks_folder = chunks_folder
        self.summaries_path = summaries_path
        self.output_folder = output_folder
        with open(self.summaries_path, "r", encoding="utf-8") as f:
            self.summaries = json.load(f)
        self.limit = limit
        self.context_step = context_step
        self.skip_existing = skip_existing
        
    def get_chunk_id_from_file(self, file):
        basename = os.path.splitext(os.path.basename(file))[0]  # Remove .txt extension
        doc_id, chunk_id = basename.split("_")[:2]
        return doc_id, chunk_id
    
    def get_adjacent_chunk_txt(self, doc_id: str, chunk_id: int) -> str:
        step = self.context_step
        adjacent_chunk_ids = [chunk_id - step, chunk_id + step]
        adjacent_chunk_files = [os.path.join(self.chunks_folder, f"{doc_id}_{i}.txt") for i in adjacent_chunk_ids]
        adjacent_chunk_txt = self.load_chunk(adjacent_chunk_files)
        return adjacent_chunk_txt
        
    def load_chunk(self, chunk_files: list[str]) -> str:
        txts = []
        for chunk_file in chunk_files:
            doc_id, chunk_id = self.get_chunk_id_from_file(chunk_file)
            if not os.path.exists(chunk_file):
                continue
            with open(chunk_file, "r", encoding="utf-8") as f:
                txt = f.read()
            txts.append(f"Chunk {chunk_id}: {txt}")
        return "\n".join(txts)
    
    async def generate_context(self, 
                               current_chunk_txt, 
                               adjacent_chunk_txt, 
                               summary_txt
        ):
        prompt = f"""
你是一个有帮助的助手，需要根据文档摘要和相邻文本块，
为当前文本块生成上下文说明。

当前文本块：
{current_chunk_txt}

文档摘要：
{summary_txt}

相邻文本块：
{adjacent_chunk_txt}

生成关于当前文本块的一句话的简短的补充描述，要求在文档摘要的背景下，结合相邻文本块，对当前文本块进行补充说明。
"""
        context = await call_llm_with_fallback(prompt)
        return context
    
    async def process_single_file(self, file, semaphore):
        """Process a single chunk file to generate its context."""
        async with semaphore:
            doc_id, chunk_id = self.get_chunk_id_from_file(file)
            output_file = os.path.join(self.output_folder, f"{doc_id}_{chunk_id}.txt")
            if self.skip_existing and os.path.exists(output_file):
                return
            
            chunk_id = int(chunk_id)
            
            current_chunk_txt = self.load_chunk([file])
            
            adjacent_chunk_txt = self.get_adjacent_chunk_txt(doc_id, chunk_id)
            summary_txt = self.summaries.get(doc_id, "")
            if summary_txt:
                summary_txt = "Summary: " + summary_txt
            try:
                context = await self.generate_context(current_chunk_txt, adjacent_chunk_txt, summary_txt)
                if context is None or not isinstance(context, str):
                    print(f"Warning: Failed to generate context for {doc_id}_{chunk_id}, skipping...")
                    return
            except Exception as e:
                print(f"Error generating context for {doc_id}_{chunk_id}: {e}, skipping...")
                return
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(context)
        
    async def run(self, max_parallel: int = 8):
        files = os.listdir(self.chunks_folder)
        if self.skip_existing:
            skip_files = set(os.listdir(self.output_folder))
            print(f"Skipping {len(skip_files)} existing files")
        else:
            skip_files = set()
        files = [os.path.join(self.chunks_folder, x) for x in files if x not in skip_files]
        print(f"Processing {len(files)} files")
        semaphore = asyncio.Semaphore(max_parallel)
        tasks = [self.process_single_file(file, semaphore) for file in files]
        if self.limit is not None:
            tasks = tasks[:self.limit]
        
        # Process tasks in parallel with progress bar
        with tqdm(total=len(tasks), desc="Generating contexts") as pbar:
            for coro in asyncio.as_completed(tasks):
                await coro
                pbar.update(1)