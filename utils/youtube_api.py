import os
import re
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# This function parses YouTube's ISO 8601 duration format (e.g., "PT2M3S")
# into a more friendly format (e.g., "2:03" or "1:05:10")
def parse_iso8601_duration(duration_str):
    if not duration_str or not duration_str.startswith('PT'):
        return "N/A"

    hours, minutes, seconds = 0, 0, 0

    # Regex to find H, M, S components
    hour_match = re.search(r'(\d+)H', duration_str)
    minute_match = re.search(r'(\d+)M', duration_str)
    second_match = re.search(r'(\d+)S', duration_str)

    if hour_match:
        hours = int(hour_match.group(1))
    if minute_match:
        minutes = int(minute_match.group(1))
    if second_match:
        seconds = int(second_match.group(1))

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def search_youtube_covers(song_query, max_results=50):
    if max_results > 50:
        max_results = 50
    
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    # 1. Search for videos to get their IDs
    request = youtube.search().list(
        q=f"{song_query} cover",
        part='snippet',
        type='video',
        maxResults=max_results,
        order='relevance'
    )
    response = request.execute()

    video_ids = [] # Collect all video IDs for a single batch request
    snippet_data = {}
    for item in response.get('items', []):
        video_ids.append(item['id']['videoId'])

    if not video_ids:
        return []

    # 2. Get all details for the found video IDs in one batch call
    #    We now request 'snippet', 'statistics', and 'contentDetails'
    video_details_request = youtube.videos().list(
        part='snippet,statistics,contentDetails',
        id=','.join(video_ids)
    )
    video_details_response = video_details_request.execute()

    videos = []
    # Loop through the full details response
    for item in video_details_response.get('items', []):
        snippet = item.get('snippet', {})
        stats = item.get('statistics', {})
        content = item.get('contentDetails', {})
        video_id = item['id']

        # Extract all data from the video.list response
        title = snippet.get('title', 'No Title')
        channel = snippet.get('channelTitle', 'No Channel')
        upload_date = snippet.get('publishedAt', '')[:10]
        thumbnail = snippet.get('thumbnails', {}).get('medium', {}).get('url')
        description = snippet.get('description', '') 

        views = int(stats.get('viewCount', 0))
        
        duration_iso = content.get('duration', None)
        duration = parse_iso8601_duration(duration_iso)

        # Fallback for thumbnail if medium isn't there
        if not thumbnail:
            thumbnail = snippet.get('thumbnails', {}).get('default', {}).get('url')

        videos.append({
            "title": title,
            "channel": channel,
            "views": views,
            "upload_date": upload_date,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": thumbnail,
            "duration": duration,
            "description": description
        })

    return videos
