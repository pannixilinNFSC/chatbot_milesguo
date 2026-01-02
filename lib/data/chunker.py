import os
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

class NaiveChunker:
    def __init__(self, 
                 input_dir="./data_miles/documents/", 
                 output_dir="./data_miles/chunks/", 
                 chunk_size=500,
                 chunk_overlap=100,
                 reload=False
                 ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.reload = reload

    def run(self):
        """Process all files in input_dir and save chunks to output_dir"""
        # Create output directory if it doesn't exist
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Get all files from input directory
        files = [os.path.join(self.input_dir, f) for f in os.listdir(self.input_dir) 
                 if os.path.isfile(os.path.join(self.input_dir, f))]
        
        # Process each file
        for file_path in tqdm(files, desc="Chunking files"):
            try:
                # Get base filename without extension
                base_name = os.path.basename(file_path)
                doc_id = os.path.splitext(base_name)[0]
                
                # Check if first chunk file exists (skip if reload=False)
                first_chunk_file = os.path.join(self.output_dir, f"{doc_id}_1.txt")
                if not self.reload and os.path.exists(first_chunk_file):
                    continue
                
                # Get chunks from the file
                chunks = self.load_data_to_paragraphs(file_path)
                
                # Save each chunk as a separate file
                for i, chunk in enumerate(chunks, start=1):
                    chunk_id = i
                    output_file = os.path.join(self.output_dir, f"{doc_id}_{chunk_id}.txt")
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(chunk)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    def load_data_to_paragraphs(self, file1):
        """Split long document into short documents within 1000 characters. 
        Because OpenAI sentence embedding ada-002 has 8000 input tokens, maximum 2000 Chinese characters.
        However, semantic encoding effectiveness decreases when approaching 2000 characters.
        """
        with open(file1, "r", encoding="utf-8") as f:
            data = f.read()
        pattern1 = r'^.*?内容梗概: '
        pattern2 = r' 友情链接：Gnews \| Gclubs \| Gfashion \| himalaya exchange \| gettr \| 法治基金 \| 新中国联邦辞典 \| $'
        data = re.sub(pattern1, "", data)
        data = re.sub(pattern2, "", data)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap
        )
        txts = text_splitter.split_text(data)
        return txts