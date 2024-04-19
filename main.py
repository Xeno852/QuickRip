import argparse
import requests
from yt_dlp import YoutubeDL

# Constants
YOUTUBE_SEARCH_API_URL = 'https://yt.lemnoslife.com/noKey/search?part=snippet&q='

def search_youtube_first_result(query):
    """Search YouTube and get JSON data for the first result."""
    params = {'q': query}
    response = requests.get(YOUTUBE_SEARCH_API_URL, params=params)

    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            print("Invalid JSON response")
    else:
        print(f"Failed to fetch results: {response.status_code}")
    return None

def get_first_result(query):
    """Extract the first video result from the search query."""
    data = search_youtube_first_result(query)
    if data and data.get('items'):
        first_item = data['items'][0]
        video_id = first_item['id']['videoId']
        title = first_item['snippet']['title']
        return video_id, title
    else:
        print("No results found or invalid response")
        return None, None

def download_video(video_id, title):
    """Download the video's audio as MP3 to the current directory."""
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{title}.%(ext)s'  # Save the file as the video title in the current directory
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def main():
    """Run the CLI tool."""
    parser = argparse.ArgumentParser(description="Download the MP3 of the first YouTube video matching the given title.")
    parser.add_argument("title", type=str, help="Title to search for on YouTube")
    args = parser.parse_args()

    video_id, video_title = get_first_result(args.title)
    if video_id:
        print(f"Downloading MP3 for video: {video_title}")
        download_video(video_id, video_title)
        print("Download complete.")
    else:
        print("Failed to find a video.")

if __name__ == '__main__':
    main()
