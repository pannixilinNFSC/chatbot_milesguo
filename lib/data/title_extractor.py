import os
import json
import re
from tqdm import tqdm


class TitleExtractor:
    """Extract and manage document titles from text files"""
    
    def __init__(self, 
                 input_dir="./data_miles/documents/", 
                 output_file="./data_miles/titles.json"):
        """
        Initialize TitleExtractor
        
        Args:
            input_dir: Directory containing text files to extract titles from
            default_output_file: Default output file path for extracted titles
        """
        self.input_dir = input_dir
        self.output_file = output_file
    
    def run(self):
        """
        Extract title of each document and organize by ID into a JSON file
        
        Args:
            input_dir: Directory containing text files (uses self.input_dir if None)
            out_file: Output file path (uses self.default_output_file if None)
        """
        files = [os.path.join(self.input_dir, x) for x in os.listdir(self.input_dir)]
        dict1 = dict()
        for in_file in tqdm(files):
            id = os.path.basename(in_file).split(".")[0]
            with open(in_file, "r") as f:
                txt = f.read()
            pattern1 = r'^(.*?)首页'
            match = re.match(pattern1, txt)
            if match: 
                title = match.group(1)
                title = title.replace("\n", " ")
            else:
                title = "unknown title"
            dict1[id] = title
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(dict1, f, indent=2, ensure_ascii=False)
    
    def load_titles(self, file=None):
        """
        Load titles from JSON file
        
        Args:
            file: Path to titles JSON file (uses self.output_file if None)
            
        Returns:
            Dictionary mapping document IDs to titles
        """
        if file is None:
            file = self.output_file
        with open(file, "r", encoding="utf-8") as f:
            dict1 = json.load(f)
        return dict1