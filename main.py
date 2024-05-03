import argparse
import os
import requests
import logging
from yt_dlp import YoutubeDL

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
YOUTUBE_SEARCH_API_URL = 'https://yt.lemnoslife.com/noKey/search?part=snippet&q='

def search_youtube_results(query, max_results=5, force_keyword=None):
    """Search YouTube and filter results based on a keyword if provided."""
    logging.info(f"Searching for '{query}' with up to {max_results} results.")
    params = {'q': query, 'maxResults': max_results}
    try:
        response = requests.get(YOUTUBE_SEARCH_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        if force_keyword:
            items = [item for item in data.get('items', []) if force_keyword.lower() in item['snippet']['title'].lower()]
            logging.info(f"Filtered {len(items)} items containing the keyword '{force_keyword}'.")
            return {'items': items}
        return data
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
    except ValueError:
        logging.error("Failed to decode JSON response")
    return None

def select_video_from_results(items):
    """Allow user to select a video from the search results."""
    logging.info("Displaying search results for selection:")
    for index, item in enumerate(items, start=1):
        title = item['snippet']['title']
        print(f"{index}: {title}")
    try:
        choice = int(input("Enter the number of the video to download: ")) - 1
        if 0 <= choice < len(items):
            selected_item = items[choice]
            return selected_item['id']['videoId'], selected_item['snippet']['title']
    except ValueError:
        logging.error("Invalid input: Please enter a valid number.")
    return None, None

def confirm_download(video_title):
    """Ask user for confirmation before downloading."""
    return input(f"Confirm download of video '{video_title}'? (y/n): ").strip().lower() == 'y'

def download_video(video_id, title, output_dir):
    """Download the video's audio as MP3 to the specified output directory."""
    logging.info(f"Preparing to download video '{title}'.")
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    output_path = os.path.join(output_dir, f'{title.replace("/", "-")}.mp3')  # Replace / in titles to avoid path issues
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'outtmpl': output_path
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    logging.info(f"Download completed and saved to {output_path}.")

def main():
    """Run the CLI tool with extended functionality and user control."""
    parser = argparse.ArgumentParser(description="Advanced YouTube MP3 downloader with various control flags.")
    parser.add_argument("query", type=str, help="Query to search for on YouTube")
    parser.add_argument("--depth", type=int, default=5, help="Number of search results to retrieve and process")
    parser.add_argument("--output", type=str, default="output", help="Directory to save the downloaded MP3 files")
    parser.add_argument("--force", type=str, help="Keyword to filter results, ensuring the keyword is present in video titles")
    parser.add_argument("--confirm", action="store_true", help="Ask for confirmation before downloading the video")
    parser.add_argument("--select", action="store_true", help="Enable selection from a list of search results")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output for detailed logs")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not os.path.exists(args.output):
        os.makedirs(args.output)
        logging.info(f"Created output directory at {args.output}")

    data = search_youtube_results(args.query, args.depth, args.force)
    if data and data.get('items'):
        items = data['items']
        video_id, video_title = (None, None)
        if args.select and items:
            video_id, video_title = select_video_from_results(items)
        elif items:
            video_id, video_title = items[0]['id']['videoId'], items[0]['snippet']['title']
            logging.info(f"Auto-selected first result: {video_title}")

        if video_id:
            if not args.confirm or (args.confirm and confirm_download(video_title)):
                download_video(video_id, video_title, args.output)
            else:
                logging.info("Download canceled by user.")
        else:
            logging.info("No suitable video found for download.")
    else:
        logging.info("No results found or invalid response.")

if __name__ == '__main__':
    main()
