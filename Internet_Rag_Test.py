import os
import requests
from urllib.parse import unquote
from bs4 import BeautifulSoup
from gpt4all import GPT4All
import datetime

# Updated Firefox configuration
FIREFOX_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://duckduckgo.com/',
    'DNT': '1'
}

def fix_duckduckgo_url(url):
    """Convert DuckDuckGo redirect URLs to proper URLs"""
    if url.startswith('//'):
        url = 'https:' + url
    if '/l/?uddg=' in url:
        url = unquote(url.split('/l/?uddg=')[1].split('&')[0])
    return url.split('&rut=')[0].split('?')[0]

def firefox_search(query, num_results=5):
    """Improved DuckDuckGo search with proper URL handling"""
    try:
        response = requests.get(
            'https://html.duckduckgo.com/html/',
            params={'q': query, 'kl': 'us-en', 'df': 'd'},
            headers=FIREFOX_HEADERS,
            timeout=10
        )
        soup = BeautifulSoup(response.text, 'lxml')
        results = []
        
        for result in soup.select('.result'):
            link = result.select_one('.result__url')
            if link:
                raw_url = link.get('href', '')
                clean_url = fix_duckduckgo_url(raw_url)
                if clean_url.startswith('http'):
                    results.append(clean_url)
            
            if len(results) >= num_results:
                break
                
        return results
    except Exception as e:
        print(f"Search error: {str(e)}")
        return []

def firefox_fetch(url):
    """Robust content extraction with error handling"""
    try:
        response = requests.get(
            url,
            headers=FIREFOX_HEADERS,
            timeout=15,
            allow_redirects=True
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove unwanted elements
        for selector in ['script', 'style', 'nav', 'footer', 
                       '.ad', '.cookie-banner', '.newsletter']:
            for element in soup.select(selector):
                element.decompose()
                
        # Prioritize main content areas
        main_content = soup.select_one('main') or soup.select_one('article') or soup
        return ' '.join(main_content.stripped_strings)[:5000]
        
    except Exception as e:
        print(f"Error fetching {url}: {str(e)[:100]}")
        return ""

def main():
    # Configuration
    MODEL_PATH = r"C:\Users\leema\AppData\Local\nomic.ai\GPT4All\Llama-3.2-3B-Instruct-Q4_0.gguf"
    
    # Initialize model once
    try:
        model = GPT4All(
            model_name=os.path.basename(MODEL_PATH),
            model_path=os.path.dirname(MODEL_PATH),
            device="gpu"
        )
    except Exception as e:
        print(f"Model load failed: {str(e)}")
        return

    # Conversation loop
    while True:
        # Get user input
        question = input("\n🔥 Firefox AI (type 'exit' to quit): ").strip()
        if question.lower() in ['exit', 'quit']:
            break
            
        # Limit question length
        question = question[:200]
        
        # Search phase
        print("\n[1/3] 🌐 Searching with Firefox engine...")
        urls = firefox_search(question)
        
        # Print found URLs before processing
        print("\n🔗 Sources being analyzed:")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
            
        # Content fetching
        print("\n[2/3] 📥 Fetching page content...")
        context = ""
        for url in urls:
            content = firefox_fetch(url)
            if content:
                context += f"SOURCE: {url}\nCONTENT: {content[:1500]}\n\n"  # Truncate long articles

        # Generate response
        print("\n[3/3] 💡 Generating answer...")
        try:
            response = model.generate(
                f"Current Date: {datetime.date.today()}\n\n"
                f"CONTEXT:\n{context[:7000]}\n\n"  # Adjust based on model's context window
                f"QUESTION: {question}\n"
                "ANSWER (be concise, cite sources):",
                max_tokens=1024,
                temp=0.4
            )
            print(f"\n{'='*50}\n📝 Response:\n{response}\n{'='*50}")
        except Exception as e:
            print(f"Generation failed: {str(e)}")

if __name__ == "__main__":
    main()