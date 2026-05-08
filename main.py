import requests
import re
import os
import sys
import logging
from urllib.parse import urlparse

# Setup logging instead of print statements
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class StoryDownloader:
    def __init__(self):
        self.api_url = "https://igsnapinsta.com/wp-admin/admin-ajax.php"
        
    def validate_url(self, url):
        """Check if URL is a valid Instagram story URL"""
        pattern = r'https?://(www\.)?instagram\.com/stories/[^/]+/\d+'
        return re.match(pattern, url) is not None
    
    def download_story(self, story_url, output_dir="downloads"):
        """Download Instagram story from URL"""
        
        if not self.validate_url(story_url):
            logging.error("Invalid Instagram story URL format")
            return None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare request
        data = {
            "action": "kdnsd_get_video",
            "social": "instagram", 
            "url": story_url
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://igsnapinsta.com",
            "Referer": "https://igsnapinsta.com/en/story"
        }
        
        logging.info(f"Processing: {story_url}")
        
        try:
            # Make API request
            response = requests.post(self.api_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get("success"):
                logging.error(f"API Error: {result.get('message', 'Unknown error')}")
                return None
            
            # Extract download URL
            html = result["data"]["html"]
            download_match = re.search(r'href="([^"]+)"[^>]*download', html)
            
            if not download_match:
                download_match = re.search(r'href="([^"]*\?url=[^"]+)"', html)
            
            if not download_match:
                logging.error("Could not extract download link")
                return None
            
            download_url = download_match.group(1)
            
            # Download the file
            logging.info("Downloading media...")
            file_response = requests.get(download_url, timeout=60)
            file_response.raise_for_status()
            
            # Determine file extension
            content_type = file_response.headers.get('content-type', '')
            if 'video' in content_type or 'mp4' in download_url:
                ext = '.mp4'
            elif 'image' in content_type or 'jpg' in download_url:
                ext = '.jpg'
            else:
                ext = '.mp4'
            
            # Generate filename
            story_id = story_url.rstrip('/').split('/')[-1].split('?')[0]
            username = story_url.split('/stories/')[1].split('/')[0]
            filename = f"{username}_{story_id}{ext}"
            filepath = os.path.join(output_dir, filename)
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(file_response.content)
            
            file_size = os.path.getsize(filepath) / 1024  # Size in KB
            logging.info(f"Successfully downloaded: {filepath} ({file_size:.1f} KB)")
            return filepath
            
        except requests.exceptions.Timeout:
            logging.error("Request timeout - server might be slow")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return None

# Command line interface for server usage
if __name__ == "__main__":
    downloader = StoryDownloader()
    
    # Support command line argument
    if len(sys.argv)> 1:
        story_url = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "downloads"
        downloader.download_story(story_url, output_dir)
    else:
        # Interactive mode (works on servers too)
        print("Instagram Story Downloader (Server Edition)")
        print("=" * 50)
        story_url = input("Enter Instagram story URL: ").strip()
        if story_url:
            downloader.download_story(story_url)
