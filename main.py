import threading
import argparse
import os
import requests
import sys
from contextlib import contextmanager
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import print_formatted_text as print
from yt_dlp import YoutubeDL

# Constants
YOUTUBE_SEARCH_API_URL = 'https://yt.lemnoslife.com/noKey/search?part=snippet&q='
download_queue = queue.Queue()

@contextmanager
def suppress_output():
    """Suppress all output by redirecting to /dev/null."""
    new_target = open(os.devnull, "w")
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = new_target, new_target
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        new_target.close()

def download_video(video_id, title, output_dir):
    """Function to download a video in a thread with suppressed output."""
    try:
        with suppress_output():
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            output_path = os.path.join(output_dir, f'{title.replace("/", "-")}.mp3')
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'outtmpl': output_path,
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        print(f"Download completed: {title}")
    except Exception as e:
        print(f"Error downloading video: {str(e)}")

def download_manager():
    """Manages downloads from the download queue."""
    while True:
        video_id, title, output_dir = download_queue.get()
        download_video(video_id, title, output_dir)
        download_queue.task_done()

def search_youtube(query, max_results=5, force_keyword=None):
    params = {'q': query, 'maxResults': max_results}
    response = requests.get(YOUTUBE_SEARCH_API_URL, params=params)
    if response.status_code == 200:
        items = response.json().get('items', [])
        if force_keyword:
            items = [item for item in items if force_keyword.lower() in item['snippet']['title'].lower()]
        return items
    return []

def main():
    parser = argparse.ArgumentParser(description="Interactive YouTube Downloader")
    parser.add_argument("--output", type=str, default="output", help="Directory to save the downloaded MP3 files")
    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    threading.Thread(target=download_manager, daemon=True).start()
    session = PromptSession()

    while True:
        query = session.prompt("Enter search query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        results = search_youtube(query, 5, '')
        if not results:
            print("No results found, try a different query.")
            continue
        for i, item in enumerate(results):
            print(f"{i+1}: {item['snippet']['title']}")
        selection = session.prompt("Select a video to download (number) or 'cancel' to cancel: ")
        if selection.lower() == 'cancel':
            continue
        try:
            selected_index = int(selection) - 1
            video_id = results[selected_index]['id']['videoId']
            video_title = results[selected_index]['snippet']['title']
            download_queue.put((video_id, video_title, args.output))
        except (IndexError, ValueError):
            print("Invalid selection. Please try again.")

if __name__ == '__main__':
    main()
