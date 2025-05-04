import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set up global headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

EXCLUDED_PATTERNS = [
    r'\.svg$', r'\.ico$', r'background', r'logo', r'icon-', r'css', r'js',
    r'\.txt$', r'\.html$', r'\.xml$', r'\.zip$'
]

IMAGE_EXTENSIONS = re.compile(r'\.(jpe?g|png|gif|bmp|webp|tiff)$', re.IGNORECASE)

def is_valid_image(filename):
    return IMAGE_EXTENSIONS.search(filename) and not any(re.search(p, filename, re.IGNORECASE) for p in EXCLUDED_PATTERNS)

def download_image(img_url, filename, output_folder, referer_url):
    try:
        filepath = os.path.join(output_folder, filename)
        if os.path.exists(filepath):
            return f"Skipping existing image: {filename}"

        headers = HEADERS.copy()
        headers['Referer'] = referer_url
        response = requests.get(img_url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            return f"Skipped non-image content: {filename}"

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        return f"Downloaded: {filename}"

    except Exception as e:
        return f"Failed to download {img_url}: {str(e)}"

def download_images_from_url(url, output_folder='downloaded_images', max_workers=10):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        a_tags = soup.find_all('a', href=True)

        image_tasks = []
        for a_tag in a_tags:
            href = a_tag['href']
            if not IMAGE_EXTENSIONS.search(href):
                continue

            filename = os.path.basename(urlparse(href).path)
            if not is_valid_image(filename):
                continue

            img_url = urljoin(url, href)
            image_tasks.append((img_url, filename))

        if not image_tasks:
            print("No valid images found.")
            return

        total_downloaded = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(download_image, img_url, filename, output_folder, url) for img_url, filename in image_tasks]
            for future in as_completed(futures):
                result = future.result()
                print(result)
                if result.startswith("Downloaded"):
                    total_downloaded += 1

        print(f"Total images downloaded: {total_downloaded}")

    except Exception as e:
        print(f"Error during scraping: {str(e)}")

if __name__ == "__main__":
    url = input("Enter the URL to scrape images from (Directory Listing): ").strip()
    output_folder = input("Enter output folder name (default is 'downloaded_images'): ").strip()
    if not output_folder:
        output_folder = 'downloaded_images'

    download_images_from_url(url, output_folder)
