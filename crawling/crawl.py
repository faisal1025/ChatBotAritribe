import os
import time
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

visited_urls = set()
saved_files = []

def get_internal_links(base_url, soup):
    internal_links = set()
    parsed_base_url = urlparse(base_url)
    base_domain = parsed_base_url.netloc

    for link in soup.find_all('a', href=True):
        href = link['href']
        parsed_url = urlparse(href)

        if parsed_url.netloc == '' or parsed_url.netloc == base_domain:
            if parsed_url.scheme == '':
                full_url = f"{parsed_base_url.scheme}://{base_domain}{href}"
            else:
                full_url = href
            internal_links.add(full_url)

    return internal_links

def save_page_content(content_url, soup, output_dir='scraped_content'):
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    cleaned_text = re.sub(r'\s+', ' ', soup.get_text(separator=' ', strip=True))
    if len(cleaned_text) < 100:
        return None
    
    parsed_url = urlparse(content_url)
    domain = parsed_url.netloc
    
    # creating safe filename
    path = parsed_url.path.replace('/', '_').replace('\\', '_')
    filename = f"{domain}{path}.txt"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_path = f"{output_dir}/{filename}"
    # Save cleaned text to file
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(cleaned_text)
        print(f"Content saved to: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        return None


def crawl_website(url, depth=2, delay=1):
    if depth == 0 or url in visited_urls:
        return None
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve {url}")
            return None
        print(f"Crawling: {url} at depth {depth}")
        print(f"response{response.text[:10]}")
        soup = BeautifulSoup(response.text, 'html.parser')
        file_path = save_page_content(url, soup)
        print(f"file_path: {file_path}")
        if file_path:
            saved_files.append(file_path)
        visited_urls.add(url)

        time.sleep(1)  # Be polite and avoid overwhelming the server

        links = get_internal_links(url, soup)
        for link in links:
            crawl_website(link, depth - 1)
        return saved_files
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        return None