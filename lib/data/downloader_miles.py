import os
import requests
import re
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from tqdm import tqdm

# Suppress BeautifulSoup encoding warnings globally
warnings.filterwarnings('ignore', category=UserWarning, module='bs4')

class MilesGuoDataDownloader:
    def __init__(self, out_folder="./data_miles/documents/", max_workers=8):
        self.urls0 = [f"https://gwins.org/cn/milesguo/list_2_{i}.html" for i in range(1,73)]
        self.out_folder = out_folder
        self.max_workers = max_workers

    def _parse_html(self, response):
        """Parse HTML content with proper encoding handling"""
        encoding = response.encoding or 'utf-8'
        try:
            content = response.content.decode(encoding, errors='replace')
        except (UnicodeDecodeError, LookupError):
            content = response.content.decode('utf-8', errors='replace')
        return BeautifulSoup(content, 'html.parser')

    def _fetch_page_urls(self, url):
        """Fetch URLs from a single page"""
        try:
            response = requests.get(url)
            if response.status_code != 200:
                return []
            
            soup = self._parse_html(response)
            link_string = '\n'.join([str(link) for link in soup.find_all('a')])
            pattern = r"/cn/milesguo/[\w/]+\.html"
            matches = re.findall(pattern, link_string)
            return [f"https://gwins.org{x}" for x in matches]
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return []

    def crawler_page_urls(self):
        """Crawl all 2866 links using multithreading"""
        urls1 = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._fetch_page_urls, url): url for url in self.urls0}
            with tqdm(total=len(self.urls0), desc="Crawling page URLs") as pbar:
                for future in as_completed(futures):
                    urls2 = future.result()
                    urls1.extend(urls2)
                    pbar.update(1)
        return urls1

    def _download_document(self, url):
        """Download and save a single document"""
        try:
            pattern = r'\d+'
            match = re.search(pattern, url)
            if not match:
                return False
            
            id = match.group()
            response = requests.get(url)
            if response.status_code != 200:
                return False
            
            soup = self._parse_html(response)
            html_doc = soup.get_text()
            html_doc = re.sub(r'\s+', ' ', html_doc)
            
            file_path = os.path.join(self.out_folder, f"{id}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_doc)
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False

    def download_documents(self):
        """Crawl all 2866 articles and save as documents using multithreading"""
        urls1 = self.crawler_page_urls()
        if not os.path.isdir(self.out_folder): 
            os.mkdir(self.out_folder)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._download_document, url): url for url in urls1}
            with tqdm(total=len(urls1), desc="Downloading documents") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)
                