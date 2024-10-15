import threading
import requests
import time

# List of URLs to scrape
urls = [
    "http://example.com",
    "http://example.org",
    "http://example.net",
    # Add more URLs as needed
]


def fetch_url(url: str):
    try:
        response = requests.get(url)
        print(f"Fetched {url} with status: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")


def fetch_all_urls():
    threads = []
    for url in urls:
        thread = threading.Thread(target=fetch_url, args=(url,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    start_time = time.time()
    fetch_all_urls()
    print(f"Multithreading duration: {time.time() - start_time:.2f} seconds")