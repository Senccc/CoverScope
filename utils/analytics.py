# utils/analytics.py
from datetime import datetime
from collections import Counter
import numpy as np
import re

def get_top_covers(videos, top_n=3):
    """Return the top N most viewed covers."""
    return sorted(videos, key=lambda v: v["views"], reverse=True)[:top_n]

def calculate_trend_score(videos):
    """
    Calculate a basic trend score based on:
    - How many covers exist
    - How recent they are
    - Total engagement (views)
    """
    if not videos:
        return 0

    now = datetime.now()
    # Convert upload dates to recency weights
    recency_scores = []
    total_views = 0

    for v in videos:
        try:
            upload_date = datetime.fromisoformat(v["upload_date"])
        except:
            upload_date = datetime.strptime(v["upload_date"], "%Y-%m-%d")

        days_ago = (now - upload_date).days
        recency = max(0, 1 - min(days_ago / 365, 1))  # 1 if recent, 0 if >1 year
        recency_scores.append(recency)
        total_views += v["views"]

    avg_recency = np.mean(recency_scores)
    num_covers = len(videos)

    # Normalize trend score (heuristic formula)
    score = (
        (avg_recency * 0.4) +
        (np.log1p(total_views) / 15 * 0.4) +
        (min(num_covers, 50) / 50 * 0.2)
    )

    return round(score * 100, 1)

def generate_trend_summary(score):
    """
    Generate a short natural-language summary based on the trend score.
    """
    if score >= 80:
        return "🔥 This song is highly trending — frequent new covers with strong engagement recently."
    elif score >= 60:
        return "📈 This song is moderately trending — cover activity and engagement are above average."
    elif score >= 40:
        return "⚖️ This song shows steady interest — consistent covers, but not rising sharply."
    elif score >= 20:
        return "📉 This song is losing traction — fewer new covers and lower engagement recently."
    else:
        return "🧊 This song has low current activity — few new covers or views recently."

def get_monthly_upload_data(videos):
    """
    Return labels (months) and counts for Chart.js visualization.
    """
    # Extract upload dates in YYYY-MM-DD format
    upload_dates = [v['upload_date'] for v in videos if 'upload_date' in v]
    
    # Convert to month-year strings like "2025-11"
    months = [datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m") for date in upload_dates]
    
    # Count how many uploads per month
    month_counts = Counter(months)
    
    # Sort by chronological order
    sorted_months = sorted(month_counts.keys())
    upload_counts = [month_counts[m] for m in sorted_months]
    
    return sorted_months, upload_counts

def classify_video_title(title: str) -> str:
    t = title.lower()
    
    # Japanese lowercase equivalents
    tj = title  # keep raw for multi-byte Japanese
    
    cover_keywords = [
        # English
        "cover", "acoustic", "band cover", "piano cover",
        "guitar cover", "drum cover", "instrumental cover",
        "vocals cover", "acoustic version", "arrangement",
        "cover version", "cover by",
        
        # Japanese
        "歌ってみた",        # tried singing (most common)
        "弾いてみた",        # tried playing (guitar/piano)
        "叩いてみた",        # tried drumming
        "弾き語り",          # acoustic self-play-and-sing
        "弾き語ってみた",    # “tried performing acoustic”
        "カバー",           # cover (JP)
        "アレンジ",         # arrangement
        "ピアノ",           # piano
        "ギター",           # guitar
        "バンドカバー",      # band cover
        "インスト",          # instrumental
        "アコースティック",   # acoustic
    ]
    
    noise_keywords = [
        # English
        "official music video", "official video", "mv", "m/v",
        "official audio", "lyric", "lyrics", "karaoke",
        "remix", "slowed", "reverb", "reaction",
        "live", "performance", "short", "shorts",
        "teaser", "trailer", "full album", "concert",
        
        # Japanese
        "公式",          # official
        "ミュージックビデオ", # music video
        "歌詞",          # lyrics
        "カラオケ",      # karaoke
        "ライブ",        # live
        "生放送",        # live stream
        "ショート",      # shorts
    ]
    
    # Covers
    for word in cover_keywords:
        if word in t or word in tj:
            return "cover"
    
    # Noise first
    for word in noise_keywords:
        if word in t or word in tj:
            return "noise"
    
    return "noise"  # ambiguous = noise
